"""语义层验证：未优化成员与优化后产物在探测点上的匹配结果必须完全一致（规范 §13.1 第 1、2 层）。

参考实现刻意走另一条路径：
- 域名：对主机名的每个后缀查三张哈希表（精确 / 含自身后缀 / 仅子域），带 ``*`` 的模式逐条用
  ``native_domain_match`` 比较——不使用优化器的 trie 与 ``covers``；
- 地址：网段按整数区间排序后二分查找——不使用 ``merge_networks``。
探测点由输入本身派生（每个模式的主机、父域、子域、相邻名字；每个网段的首尾与外侧地址），
覆盖所有边界；有限探测是交叉检验，不替代 §9.3 的推导与属性测试。
classical 只做文档化的变换（去重、关键字包含、端口合并），逐条核对每个输入条件仍被表达。
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.rule import Condition, Leaf, Member, render_member
from domainrouter_v2.planner import Artifact
from domainrouter_v2.verify.reference import native_domain_match

_PROBE_LABEL = "probe-x9"
_PORT_TYPES = ("DST-PORT", "SRC-PORT", "IN-PORT")


@dataclass(slots=True)
class SemanticResult:
    artifact: str
    domain_probes: int = 0
    ip_probes: int = 0
    mismatches: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatches


class DomainOracle:
    def __init__(self, patterns: list[DomainPattern]) -> None:
        self.exact: set[str] = set()
        self.suffix: set[str] = set()
        self.subonly: set[str] = set()
        self.wild: list[str] = []
        for pattern in patterns:
            native = pattern.to_native()
            if "*" in native:
                self.wild.append(native)
            elif native.startswith("+."):
                self.suffix.add(native[2:])
            elif native.startswith("."):
                self.subonly.add(native[1:])
            else:
                self.exact.add(native)

    def matches(self, host: str) -> bool:
        if host in self.exact or host in self.suffix:
            return True
        labels = host.split(".")
        for index in range(1, len(labels)):
            parent = ".".join(labels[index:])
            if parent in self.suffix or parent in self.subonly:
                return True
        return any(native_domain_match(w, host) for w in self.wild)


class NetworkOracle:
    """区间未合并、可能重叠。地址被覆盖 ⇔ 起点 ≤ 地址的区间中，最大终点 ≥ 地址。"""

    def __init__(self, networks: list[Network]) -> None:
        self.starts: dict[int, list[int]] = {}
        self.max_end: dict[int, list[int]] = {}
        for version in (4, 6):
            ranges = sorted((n.first, n.last) for n in networks if n.version == version)
            self.starts[version] = [first for first, _ in ranges]
            running, ends = -1, []
            for _, last in ranges:
                running = max(running, last)
                ends.append(running)
            self.max_end[version] = ends

    def matches(self, version: int, address: int) -> bool:
        index = bisect.bisect_right(self.starts[version], address)
        return index > 0 and self.max_end[version][index - 1] >= address


def domain_probes(patterns: list[DomainPattern]) -> set[str]:
    probes: set[str] = set()
    for pattern in patterns:
        lits = dict(pattern.literals)
        labels = [lits.get(pos, "zz") for pos in reversed(range(pattern.fixed_length))]
        host = ".".join(labels)
        extra = ["zz"] * (pattern.min_labels - pattern.fixed_length)
        base = ".".join([*extra, host])
        probes.update(
            {
                base,
                f"{_PROBE_LABEL}.{base}",
                f"a.{_PROBE_LABEL}.{base}",
                host,
                ".".join(labels[1:]) if len(labels) > 1 else host,
                f"x{host}",
            }
        )
    return probes


def ip_probes(networks: list[Network]) -> set[tuple[int, int]]:
    probes: set[tuple[int, int]] = set()
    top = {4: (1 << 32) - 1, 6: (1 << 128) - 1}
    for n in networks:
        for address in (n.first - 1, n.first, (n.first + n.last) // 2, n.last, n.last + 1):
            if 0 <= address <= top[n.version]:
                probes.add((n.version, address))
    return probes


def verify_artifact(artifact: Artifact, raw: list[Member]) -> SemanticResult:
    result = SemanticResult(" + ".join(artifact.collections))
    raw_domains = [m for m in raw if isinstance(m, DomainPattern)]
    raw_networks = [m for m in raw if isinstance(m, Network)]
    raw_conditions = [m for m in raw if not isinstance(m, DomainPattern | Network)]

    before, after = DomainOracle(raw_domains), DomainOracle(artifact.domains)
    for host in sorted(domain_probes(raw_domains) | domain_probes(artifact.domains)):
        result.domain_probes += 1
        if before.matches(host) != after.matches(host):
            result.mismatches.append(f"域名 {host}：优化前 {before.matches(host)}，优化后相反")

    net_before, net_after = NetworkOracle(raw_networks), NetworkOracle(artifact.networks)
    for version, address in sorted(ip_probes(raw_networks) | ip_probes(artifact.networks)):
        result.ip_probes += 1
        if net_before.matches(version, address) != net_after.matches(version, address):
            result.mismatches.append(f"地址 IPv{version} {address}：优化前后结果不同")

    result.mismatches.extend(_check_classical(raw_conditions, artifact.conditions))
    return result


def _check_classical(raw: list[Condition], optimized: list[Condition]) -> list[str]:
    out: list[str] = []
    kept = set(optimized)
    keywords = [c.payload for c in optimized if isinstance(c, Leaf) and c.type == "DOMAIN-KEYWORD"]
    ports = {
        c.type: _ranges(c.payload)
        for c in optimized
        if isinstance(c, Leaf) and c.type in _PORT_TYPES
    }
    for condition in raw:
        if condition in kept:
            continue
        if (
            isinstance(condition, Leaf)
            and condition.type == "DOMAIN-KEYWORD"
            and any(k in condition.payload for k in keywords)
        ):
            continue
        if isinstance(condition, Leaf) and condition.type in _PORT_TYPES:
            merged = ports.get(condition.type, [])
            if all(
                any(lo <= a and b <= hi for lo, hi in merged) for a, b in _ranges(condition.payload)
            ):
                continue
        out.append(f"classical 条件丢失：{render_member(condition)}")
    for condition in optimized:
        if condition in set(raw):
            continue
        if isinstance(condition, Leaf) and condition.type in _PORT_TYPES:
            covered = [
                r
                for c in raw
                if isinstance(c, Leaf) and c.type == condition.type
                for r in _ranges(c.payload)
            ]
            if all(
                any(lo <= a and b <= hi for lo, hi in _merge(covered))
                for a, b in _ranges(condition.payload)
            ):
                continue
        out.append(f"classical 出现输入中没有的条件：{render_member(condition)}")
    return out


def _ranges(payload: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for part in payload.split("/"):
        low, _, high = part.partition("-")
        out.append((int(low), int(high or low)))
    return out


def _merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for low, high in sorted(ranges):
        if merged and low <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged
