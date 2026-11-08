"""命中解释：给定主机名或 IP，按 ``[Rules]`` 顺序说明会命中哪条路由、由哪条规则命中。

只用已知元数据求值：域名集合、地址集合、关键字可确定；正则、GEOSITE、GEOIP、进程等
依赖内核或外部数据的条件标记为「无法在此确定」，结论随之变为条件性的，而不是假装完成路由判定。
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field

from domainrouter_v2.build import BuildResult
from domainrouter_v2.model.domain import DomainError, normalize_host
from domainrouter_v2.model.profile import RouteKind
from domainrouter_v2.model.rule import Condition, Leaf
from domainrouter_v2.planner import Artifact, route_blocks
from domainrouter_v2.verify.semantic import DomainOracle, NetworkOracle

_TARGET_IP_TYPES = frozenset({"GEOIP", "IP-ASN", "IP-SUFFIX"})


@dataclass(slots=True)
class RouteHit:
    index: int
    route: str
    target: str
    matched_by: str
    certain: bool


@dataclass(slots=True)
class Explanation:
    query: str
    hits: list[RouteHit] = field(default_factory=list)
    undecidable: list[RouteHit] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"查询：{self.query}"]
        winner = min(self.hits, key=lambda h: h.index)  # MATCH 保证至少一条确定命中
        lines.append(
            f"结论：[{winner.index}] {winner.route} → {winner.target}（{winner.matched_by}）"
        )
        earlier = sorted(
            (h for h in self.undecidable if h.index < winner.index), key=lambda h: h.index
        )
        if earlier:
            lines.append(
                "更早的路由含无法在此确定的条件（端口、进程、地理数据等），实际结果可能不同："
            )
            lines += [f"  [{h.index}] {h.route} → {h.target}：{h.matched_by}" for h in earlier]
        shadowed = [h for h in self.hits if h.index > winner.index and h.route != "MATCH"]
        if shadowed:
            names = "、".join(f"[{h.index}] {h.route}" for h in shadowed)
            lines.append(f"同样会命中、但被前面遮挡的路由：{names}")
        return "\n".join(lines)


def explain(result: BuildResult, *, host: str | None = None, ip: str | None = None) -> Explanation:
    assert result.profile is not None and result.plan is not None
    query = host or ip or ""
    explanation = Explanation(query)
    normalized_host = None
    address = None
    if host is not None:
        try:
            normalized_host = normalize_host(host.rstrip("."))
        except DomainError as exc:
            raise ValueError(str(exc)) from exc
    if ip is not None:
        address = ipaddress.ip_address(ip)
    blocks = {start: names for start, names in route_blocks(result.profile)}
    for route in result.profile.routes:
        if route.kind is RouteKind.COLLECTION:
            names = blocks.get(route.index)
            if names is None:
                continue
            artifact = result.plan.artifacts[names]
            label = " + ".join(names)
            verdict = _artifact_verdict(artifact, normalized_host, address)
            if verdict is not None:
                matched_by, certain = verdict
                hit = RouteHit(route.index, label, route.target, matched_by, certain)
                (explanation.hits if certain else explanation.undecidable).append(hit)
        elif route.kind is RouteKind.INLINE and route.condition is not None:
            decision = _condition(route.condition, normalized_host, address)
            if decision is not False:
                certain = decision is True
                hit = RouteHit(route.index, route.inline_text, route.target, "内联规则", certain)
                (explanation.hits if certain else explanation.undecidable).append(hit)
        else:
            explanation.hits.append(RouteHit(route.index, "MATCH", route.target, "兜底", True))
    return explanation


def _artifact_verdict(
    artifact: Artifact,
    host: str | None,
    address: ipaddress.IPv4Address | ipaddress.IPv6Address | None,
) -> tuple[str, bool] | None:
    if host is not None and DomainOracle(artifact.domains).matches(host):
        return "domain 集合", True
    if address is not None and NetworkOracle(artifact.networks).matches(
        address.version, int(address)
    ):
        return "ipcidr 集合", True
    unknown: list[str] = []
    for condition in artifact.conditions:
        decision = _condition(condition, host, address)
        if decision is True:
            return f"classical：{condition.render()}", True
        if decision is None:
            unknown.append(condition.render())
    if unknown:
        return f"classical 中有 {len(unknown)} 条条件无法在此确定，例如 {unknown[0]}", False
    return None


def _condition(
    condition: Condition,
    host: str | None,
    address: ipaddress.IPv4Address | ipaddress.IPv6Address | None,
) -> bool | None:
    """True 命中 / False 不命中 / None 无法在此确定。"""
    if not isinstance(condition, Leaf):
        return None
    if condition.type == "DOMAIN-KEYWORD":
        return host is not None and condition.payload in host
    if condition.type == "DOMAIN":
        return host == condition.payload
    if condition.type == "DOMAIN-SUFFIX":
        return host is not None and (
            host == condition.payload or host.endswith("." + condition.payload)
        )
    if condition.type in {"IP-CIDR", "IP-CIDR6"}:
        if address is None:
            return False if "no-resolve" in condition.params else None
        return address in ipaddress.ip_network(condition.payload)
    if condition.type in _TARGET_IP_TYPES and address is None and "no-resolve" in condition.params:
        return False  # 只知道域名、目标 IP 未知：no-resolve 条件不会触发解析，因此不命中
    return None
