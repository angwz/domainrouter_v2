"""classical 优化：精确去重、关键字包含消除、端口合并与成本排序（merge-cases §1、§7）。

为什么可以在 classical 内任意重排与去重：一个 classical provider 对一次连接只返回「是否命中」，
各成员之间是并集；本项目给所有目标 IP 条件加 no-resolve，剩下唯一的副作用是 PROCESS/UID
可能触发进程查询，而查询结果在一次连接内只取一次，不会让其他条件的结果改变。
因此重排只改变成本，不改变结果。逻辑表达式（AND/OR/NOT）内部不做任何改写。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from domainrouter_v2.model.rule import Condition, Leaf
from domainrouter_v2.registry import TYPES

_PORT_TYPES = ("DST-PORT", "SRC-PORT", "IN-PORT")


@dataclass(slots=True)
class ClassicalEvents:
    duplicates: int = 0
    covered: dict[Condition, Condition] = field(default_factory=dict)
    merged: dict[Condition, tuple[Condition, ...]] = field(default_factory=dict)


def optimize_classical(conditions: list[Condition]) -> tuple[list[Condition], ClassicalEvents]:
    events = ClassicalEvents()
    unique = list(dict.fromkeys(conditions))
    events.duplicates = len(conditions) - len(unique)
    unique = _remove_covered_keywords(unique, events)
    unique = _merge_ports(unique, events)
    return sorted(unique, key=_cost_key), events


def _cost_key(condition: Condition) -> tuple[int, str]:
    name = condition.type if isinstance(condition, Leaf) else condition.op
    return (TYPES[name].rank, condition.render())


def _remove_covered_keywords(
    conditions: list[Condition], events: ClassicalEvents
) -> list[Condition]:
    """关键字 k2 含有另一个关键字 k1 时，任何命中 k2 的主机名都命中 k1，k2 冗余。"""
    keywords = sorted(
        (c for c in conditions if isinstance(c, Leaf) and c.type == "DOMAIN-KEYWORD"),
        key=lambda c: (len(c.payload), c.payload),
    )
    kept: list[Leaf] = []
    for keyword in keywords:
        coverer = next((k for k in kept if k.payload in keyword.payload), None)
        if coverer is None:
            kept.append(keyword)
        else:
            events.covered[keyword] = coverer
    return [c for c in conditions if c not in events.covered]


def _merge_ports(conditions: list[Condition], events: ClassicalEvents) -> list[Condition]:
    """同一类型的端口条件合并为一条（``80/443/1000-2000``），区间精确并集。"""
    by_type: dict[str, list[Leaf]] = defaultdict(list)
    for condition in conditions:
        if isinstance(condition, Leaf) and condition.type in _PORT_TYPES:
            by_type[condition.type].append(condition)
    result = [c for c in conditions if not (isinstance(c, Leaf) and c.type in by_type)]
    for port_type, leaves in by_type.items():
        ranges = sorted(r for leaf in leaves for r in _ranges(leaf.payload))
        merged: list[tuple[int, int]] = []
        for low, high in ranges:
            if merged and low <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], high))
            else:
                merged.append((low, high))
        text = "/".join(str(lo) if lo == hi else f"{lo}-{hi}" for lo, hi in merged)
        combined = Leaf(port_type, text)
        result.append(combined)
        if len(leaves) > 1 or leaves[0] != combined:
            events.merged[combined] = tuple(leaves)
    return result


def _ranges(payload: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for part in payload.split("/"):
        low, _, high = part.partition("-")
        out.append((int(low), int(high or low)))
    return out
