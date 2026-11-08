"""合并溯源：每条输出规则来自哪些来源，以及它合并、覆盖了哪些输入。

溯源不复用优化过程的中间状态作为唯一依据，而是对每条输入独立地找出「代表它的那条输出」：
- 输入原样保留 → 就是它自己；
- domain：在输出上建覆盖索引，找覆盖它的输出（``DomainPattern.covers`` 精确判定）；
- ipcidr：输出是不相交的对齐 CIDR，输入落在唯一一条输出之内（二分查找后校验包含）；
- classical：按优化事件（关键字被包含、端口合并）找到代表。

优化器保证每条输入都被某一条输出完整包含（合并只产生其组成部分的超集，消除只删除被单条
模式覆盖的条目）。找不到时说明合并算法有误，构建会给出警告，并在注释中如实缺失。
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.rule import Member
from domainrouter_v2.optimize.domain import CoverIndex
from domainrouter_v2.planner import Artifact

HANDWRITTEN = "my.wei"


@dataclass(frozen=True, slots=True)
class Trace:
    """一条输出规则的来历。来源用标签表示：来源 URL，或手写的 ``my.wei``。"""

    own: frozenset[str]  # 输出原样出现在哪些来源中；由合并新生成的条目为空
    merged: tuple[tuple[Member, frozenset[str]], ...]  # 合成它的输入
    covered: tuple[tuple[Member, frozenset[str]], ...]  # 被它覆盖而删去的输入


@dataclass(slots=True)
class ArtifactTrace:
    traces: dict[Member, Trace] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)  # 来源标签的声明顺序
    unlocated: list[Member] = field(default_factory=list)  # 找不到代表的输入（应为空）


def trace_artifact(
    artifact: Artifact, origins: dict[Member, set[str]], labels: list[str]
) -> ArtifactTrace:
    """origins：该块全部输入成员 → 来源标签（多个合集已合并）。"""
    result = ArtifactTrace(labels=labels)
    domains: dict[Member, set[str]] = {}
    networks: dict[Member, set[str]] = {}
    conditions: dict[Member, set[str]] = {}
    for member, sources in origins.items():
        if isinstance(member, DomainPattern):
            domains[member] = sources
        elif isinstance(member, Network):
            networks[member] = sources
        else:
            conditions[member] = sources

    index = CoverIndex(artifact.domains)

    def locate_domain(member: Member) -> Member | None:
        return index.coverer(member) if isinstance(member, DomainPattern) else None

    domain_parts: set[Member] = {
        part for parts in artifact.domain_events.merged.values() for part in parts
    }
    _trace(result, artifact.domains, domains, locate_domain, domain_parts.__contains__)

    _trace(result, artifact.networks, networks, _network_locator(artifact.networks), None)

    events = artifact.classical_events
    merged_into = {part: out for out, parts in events.merged.items() for part in parts}

    def locate_condition(member: Member) -> Member | None:
        if isinstance(member, DomainPattern | Network):
            return None
        return events.covered.get(member) or merged_into.get(member)

    classical_parts: set[Member] = set(merged_into)
    _trace(result, artifact.conditions, conditions, locate_condition, classical_parts.__contains__)
    return result


def _trace(
    result: ArtifactTrace,
    outputs: Iterable[Member],
    origins: dict[Member, set[str]],
    locate: Callable[[Member], Member | None],
    is_part: Callable[[Member], bool] | None,
) -> None:
    """is_part：被吸收的输入是否属于「合成」该输出的部分；None 表示由输出是否原样存在决定。"""
    absorbed: dict[Member, list[Member]] = {}
    outputs = list(outputs)
    present = set(outputs)
    for member in origins:
        if member in present:
            continue
        target = locate(member)
        if target is None or target not in present:
            result.unlocated.append(member)
        else:
            absorbed.setdefault(target, []).append(member)
    for output in outputs:
        own = frozenset(origins.get(output, ()))
        merged: list[tuple[Member, frozenset[str]]] = []
        covered: list[tuple[Member, frozenset[str]]] = []
        for member in absorbed.get(output, ()):
            entry = (member, frozenset(origins[member]))
            synthesized = not own if is_part is None else is_part(member)
            (merged if synthesized else covered).append(entry)
        result.traces[output] = Trace(own, tuple(merged), tuple(covered))


def _network_locator(outputs: list[Network]) -> Callable[[Member], Member | None]:
    ordered = sorted(outputs, key=lambda n: (n.version, n.first))
    keys = [(n.version, n.first) for n in ordered]

    def locate(member: Member) -> Member | None:
        assert isinstance(member, Network)
        i = bisect.bisect_right(keys, (member.version, member.first)) - 1
        if i < 0:
            return None
        candidate = ordered[i]
        inside = (
            candidate.version == member.version
            and candidate.first <= member.first
            and member.last <= candidate.last
        )
        return candidate if inside else None

    return locate
