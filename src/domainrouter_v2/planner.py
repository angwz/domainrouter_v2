"""输出规划：路由块、分区、文件命名与 rulesets 条目（merge-cases §9）。

路由块：``[Rules]`` 中相邻且目标策略组相同的合集引用合并为一块，共用一组文件。
连续指向同一目标的规则取并集后命中结果不变，而 RULE-SET 数量减少（decisions/0001 #10）。

命名：provider 名由 subconverter 的 ``findFileName`` 从 URL 文件名去掉扩展名得到，
重名时追加 ``_2``；客户端缓存路径又依赖该名字，Windows 上大小写不敏感。
因此三个分区的 stem（``X``、``X-ipcidr``、``X-classic``）在全局按大小写折叠后必须唯一，
冲突的块改用确定性的哈希 stem，迭代直到唯一。
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from domainrouter_v2.diagnostics import Code, Diagnostic, error, warning
from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network, merge_networks
from domainrouter_v2.model.profile import Profile, RouteKind
from domainrouter_v2.model.rule import Condition, Member
from domainrouter_v2.optimize.classical import ClassicalEvents, optimize_classical
from domainrouter_v2.optimize.domain import DomainEvents, optimize_domains

SUBCONVERTER_RULESET_LIMIT = 64
_SAFE_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)


@dataclass(frozen=True, slots=True)
class Partition:
    behavior: str  # domain / ipcidr / classical
    directory: str  # clash-domain / clash-ipcidr / clash-classic
    toml_type: str  # clash-domain / clash-ipcidr / clash-classic
    suffix: str  # 文件名后缀


DOMAIN = Partition("domain", "clash-domain", "clash-domain", "")
IPCIDR = Partition("ipcidr", "clash-ipcidr", "clash-ipcidr", "-ipcidr")
CLASSICAL = Partition("classical", "clash-classic", "clash-classic", "-classic")
PARTITIONS = (DOMAIN, IPCIDR, CLASSICAL)


@dataclass(slots=True)
class Artifact:
    """一个路由块的产物：最多三个非空分区。"""

    collections: tuple[str, ...]
    stem: str
    domains: list[DomainPattern]
    networks: list[Network]
    conditions: list[Condition]
    input_count: int
    domain_events: DomainEvents
    classical_events: ClassicalEvents
    network_input: int

    def members(self, partition: Partition) -> list[Member]:
        if partition is DOMAIN:
            return list(self.domains)
        if partition is IPCIDR:
            return list(self.networks)
        return list(self.conditions)

    def partitions(self) -> list[Partition]:
        return [p for p in PARTITIONS if self.members(p)]

    def path(self, partition: Partition) -> str:
        return f"{partition.directory}/{self.stem}{partition.suffix}.yaml"


@dataclass(frozen=True, slots=True)
class RulesetEntry:
    group: str
    ruleset: str
    type: str = ""
    interval: int = 0

    def as_toml(self) -> dict[str, str | int]:
        table: dict[str, str | int] = {"group": self.group, "ruleset": self.ruleset}
        if self.type:
            table["type"] = self.type
            table["interval"] = self.interval
        return table


@dataclass(slots=True)
class Plan:
    artifacts: dict[tuple[str, ...], Artifact] = field(default_factory=dict)
    rulesets: list[RulesetEntry] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def route_blocks(profile: Profile) -> list[tuple[int, tuple[str, ...]]]:
    """返回 (首条路由序号, 合集名元组)。相邻且目标相同的合集引用归为一块。"""
    blocks: list[tuple[int, tuple[str, ...]]] = []
    previous_target: str | None = None
    for route in profile.routes:
        if route.kind is not RouteKind.COLLECTION:
            previous_target = None
            continue
        if blocks and previous_target == route.target:
            start, names = blocks[-1]
            if route.collection not in names:
                blocks[-1] = (start, (*names, route.collection))
        else:
            blocks.append((route.index, (route.collection,)))
        previous_target = route.target
    return blocks


def build_plan(
    profile: Profile,
    members: dict[str, list[Member]],
    *,
    resource_url: Callable[[str], str],
    interval: int,
    allow_empty: frozenset[str],
) -> Plan:
    """members：每个合集解析后的全部成员（本地 + 来源），按来源声明顺序。"""
    plan = Plan()
    blocks = route_blocks(profile)
    block_of_route: dict[int, tuple[str, ...]] = {}
    for start, names in blocks:
        block_of_route[start] = names
        if names not in plan.artifacts:
            plan.artifacts[names] = _make_artifact(names, members)
    _assign_stems(plan)

    for route in profile.routes:
        if route.kind is RouteKind.COLLECTION:
            names_for_route = block_of_route.get(route.index)
            if names_for_route is None:
                continue  # 已并入前一块
            artifact = plan.artifacts[names_for_route]
            parts = artifact.partitions()
            if not parts:
                if set(names_for_route) <= allow_empty:
                    continue
                plan.diagnostics.append(
                    error(
                        Code.EMPTY_COLLECTION,
                        f"合集 {' + '.join(names_for_route)} 被 [Rules] 引用但没有任何有效规则",
                        route.span,
                        "检查来源是否可用，或在 policy.allow_empty_collections 中允许为空",
                    )
                )
                continue
            for partition in parts:
                plan.rulesets.append(
                    RulesetEntry(
                        route.target,
                        resource_url(artifact.path(partition)),
                        partition.toml_type,
                        interval,
                    )
                )
        else:
            plan.rulesets.append(RulesetEntry(route.target, "[]" + route.inline_text))

    unreferenced = [name for name in profile.collections if name not in profile.referenced]
    for name in unreferenced:
        plan.diagnostics.append(
            warning(
                Code.UNREFERENCED_COLLECTION,
                f"合集 [{name}] 未被 [Rules] 引用，不生成文件",
                profile.collections[name].span,
            )
        )
    if len(plan.rulesets) > SUBCONVERTER_RULESET_LIMIT:
        plan.diagnostics.append(
            warning(
                Code.RULESET_LIMIT,
                f"rulesets.toml 共 {len(plan.rulesets)} 条，超过 subconverter 外部配置的 "
                f"{SUBCONVERTER_RULESET_LIMIT} 条上限；在 pref 中直接导入不受此限",
            )
        )
    return plan


def _make_artifact(names: tuple[str, ...], members: dict[str, list[Member]]) -> Artifact:
    domains: list[DomainPattern] = []
    networks: list[Network] = []
    conditions: list[Condition] = []
    for name in names:
        for member in members.get(name, []):
            if isinstance(member, DomainPattern):
                domains.append(member)
            elif isinstance(member, Network):
                networks.append(member)
            else:
                conditions.append(member)
    optimized_domains, domain_events = optimize_domains(domains)
    optimized_conditions, classical_events = optimize_classical(conditions)
    return Artifact(
        collections=names,
        stem="",
        domains=optimized_domains,
        networks=merge_networks(networks),
        conditions=optimized_conditions,
        input_count=len(domains) + len(networks) + len(conditions),
        domain_events=domain_events,
        classical_events=classical_events,
        network_input=len(networks),
    )


def preferred_stem(names: tuple[str, ...]) -> str:
    candidate = "__".join(names)
    if all(_is_safe(name) for name in names) and _is_safe(candidate):
        return candidate
    return hashed_stem(names)


def hashed_stem(names: tuple[str, ...]) -> str:
    digest = hashlib.sha256("\x00".join(names).encode("utf-8")).hexdigest()
    return f"c-{digest[:20]}"


def _is_safe(name: str) -> bool:
    return bool(_SAFE_STEM.match(name)) and name.lower() not in _WINDOWS_RESERVED


def _assign_stems(plan: Plan) -> None:
    """为每块分配 stem；provider 名（含分区后缀）大小写折叠后冲突的块改用哈希 stem。"""
    hashed: set[tuple[str, ...]] = set()
    while True:
        for names, artifact in plan.artifacts.items():
            artifact.stem = hashed_stem(names) if names in hashed else preferred_stem(names)
        owners: dict[str, set[tuple[str, ...]]] = {}
        for names, artifact in plan.artifacts.items():
            for partition in artifact.partitions():
                key = f"{artifact.stem}{partition.suffix}".casefold()
                owners.setdefault(key, set()).add(names)
        clashes = {n for group in owners.values() if len(group) > 1 for n in group}
        if not clashes - hashed:
            if clashes:
                raise RuntimeError("哈希 stem 仍然冲突")  # SHA-256 前缀碰撞，实际不可能
            return
        hashed |= clashes
