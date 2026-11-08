"""domain 集合优化：去重、包含消除与精确合并，迭代到固定点（规范 §9.2、§9.3）。

保证：输出语言 = 输入语言，且输出中没有任何一条被另一条完整包含。

候选索引：所有模式按「从右往左的固定标签序列」（ANY 记为 ``*``）建一棵 trie。
为模式 P 找覆盖者 Q 时，Q 在每个位置必须是 ANY 或与 P 相同的 literal，
因此从根出发只沿两类子节点下行：与 P 该位置 literal 相同的子节点、``*`` 子节点。
P 在某位置是 ANY 时只能沿 ``*`` 下行。Q 的固定长度不会超过 P 的最少层数。
这一遍历不会漏掉任何候选（完备），再用 ``DomainPattern.covers`` 精确判定。
常规输入不含 ``*``，每个模式的查找只走一条路径，总成本与标签总数成正比。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from domainrouter_v2.model.domain import DomainPattern

_ANY = "*"


@dataclass(slots=True)
class DomainEvents:
    """优化事件：被覆盖（被谁）与合并（由哪些合成）。"""

    covered: dict[DomainPattern, DomainPattern] = field(default_factory=dict)
    merged: dict[DomainPattern, tuple[DomainPattern, ...]] = field(default_factory=dict)
    duplicates: int = 0


@dataclass(slots=True)
class _Node:
    children: dict[str, _Node] = field(default_factory=dict)
    patterns: list[DomainPattern] = field(default_factory=list)


def optimize_domains(
    patterns: list[DomainPattern],
) -> tuple[list[DomainPattern], DomainEvents]:
    """返回 (按 sort_key 排序的结果, 事件)。"""
    events = DomainEvents()
    unique = set(patterns)
    events.duplicates = len(patterns) - len(unique)
    current = unique
    while True:
        merged = _merge(current, events)
        reduced = _remove_covered(merged, events)
        if reduced == current:
            break
        current = reduced
    _resolve_chains(events, current)
    return sorted(current, key=DomainPattern.sort_key), events


def _fixed_labels(pattern: DomainPattern) -> tuple[str, ...]:
    lits = dict(pattern.literals)
    return tuple(lits.get(pos, _ANY) for pos in range(pattern.fixed_length))


def _merge(patterns: set[DomainPattern], events: DomainEvents) -> set[DomainPattern]:
    """同一 literal 表内，长度区间相交或相邻且并集可表达为单个原生模式时合并。"""
    groups: dict[tuple[tuple[int, str], ...], list[DomainPattern]] = defaultdict(list)
    for pattern in patterns:
        groups[pattern.literals].append(pattern)
    result: set[DomainPattern] = set()
    for group in groups.values():
        if len(group) == 1:
            result.add(group[0])
            continue
        group.sort(key=lambda p: (p.min_labels, p.max_labels is None, p.max_labels or 0))
        acc = group[0]
        sources = [acc]
        for pattern in group[1:]:
            union = acc.union(pattern)
            if union is None:
                _flush(result, acc, sources, events)
                acc, sources = pattern, [pattern]
            else:
                acc = union
                sources.append(pattern)
        _flush(result, acc, sources, events)
    return result


def _flush(
    result: set[DomainPattern],
    acc: DomainPattern,
    sources: list[DomainPattern],
    events: DomainEvents,
) -> None:
    result.add(acc)
    if len(sources) > 1 or sources[0] != acc:
        parts: list[DomainPattern] = []
        for source in sources:
            parts.extend(events.merged.pop(source, (source,)))
        events.merged[acc] = tuple(sorted(set(parts), key=DomainPattern.sort_key))


def _remove_covered(patterns: set[DomainPattern], events: DomainEvents) -> set[DomainPattern]:
    root = _Node()
    for pattern in patterns:
        node = root
        for label in _fixed_labels(pattern):
            node = node.children.setdefault(label, _Node())
        node.patterns.append(pattern)
    survivors: set[DomainPattern] = set()
    for pattern in patterns:
        coverer = _find_coverer(root, pattern)
        if coverer is None:
            survivors.add(pattern)
        else:
            events.covered[pattern] = coverer
    return survivors


def _find_coverer(root: _Node, target: DomainPattern) -> DomainPattern | None:
    """深度优先查找任一不同于 target 且覆盖它的模式。"""
    lits = dict(target.literals)
    stack: list[tuple[_Node, int]] = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        for candidate in node.patterns:
            if candidate != target and candidate.covers(target):
                return candidate
        if depth >= target.min_labels:
            continue
        literal = lits.get(depth)
        wildcard = node.children.get(_ANY)
        if wildcard is not None:
            stack.append((wildcard, depth + 1))
        if literal is not None:
            exact = node.children.get(literal)
            if exact is not None:
                stack.append((exact, depth + 1))
    return None


def _resolve_chains(events: DomainEvents, survivors: set[DomainPattern]) -> None:
    """把覆盖链归约到仍存在的代表：覆盖者自身被覆盖或被合并时继续追溯（规范 §11.5）。"""
    merged_into: dict[DomainPattern, DomainPattern] = {}
    for result, parts in events.merged.items():
        for part in parts:
            merged_into[part] = result
    for pattern in list(events.covered):
        seen: set[DomainPattern] = set()
        coverer = events.covered[pattern]
        while coverer not in survivors and coverer not in seen:
            seen.add(coverer)
            coverer = events.covered.get(coverer) or merged_into.get(coverer, coverer)
        events.covered[pattern] = coverer
    for result in list(events.merged):
        if result not in survivors:
            del events.merged[result]
