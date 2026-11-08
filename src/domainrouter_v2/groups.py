"""策略组 ``groups.toml`` 的校验（subconverter ``[[custom_groups]]`` 结构）。

字段约束来自 angwz/subconverter@a33d49e ``src/config/binding.h``：
- ``name``、``type`` 必填，type ∈ select/url-test/load-balance/fallback/relay/ssid；
- url-test、fallback、load-balance 必须有 ``url`` 与 ``interval``；
- 至少有 ``rule`` 或 ``use`` 之一。
``rule`` 中 ``[]名称`` 引用其他组或内置策略，其他条目是匹配节点名的正则。
输出时原样复制文件（只统一换行），不重排、不改写用户的定义。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field

from domainrouter_v2.diagnostics import Code, Diagnostic, SourceSpan, error, warning

BUILTIN_TARGETS = frozenset({"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE"})
GROUP_TYPES = frozenset({"select", "url-test", "load-balance", "fallback", "relay", "ssid"})
_NEEDS_PROBE = frozenset({"url-test", "fallback", "load-balance"})


@dataclass(slots=True)
class GroupsResult:
    names: list[str] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def validate_groups(text: str, origin: str) -> GroupsResult:
    result = GroupsResult()
    span = SourceSpan(origin, 1)
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        result.diagnostics.append(error(Code.GROUP_INVALID, f"TOML 语法错误：{exc}", span))
        return result
    groups = data.get("custom_groups")
    if not isinstance(groups, list) or not groups:
        result.diagnostics.append(error(Code.GROUP_INVALID, "缺少 [[custom_groups]]", span))
        return result
    references: dict[str, list[str]] = {}
    for index, group in enumerate(groups, 1):
        where = SourceSpan(origin, 0, f"custom_groups[{index}]")
        name = group.get("name") if isinstance(group, dict) else None
        if not isinstance(name, str) or not name:
            result.diagnostics.append(error(Code.GROUP_INVALID, "组缺少 name", where))
            continue
        _check_group(name, group, where, result)
        if name in references:
            result.diagnostics.append(error(Code.GROUP_INVALID, f"组名重复：{name}", where))
        references[name] = [
            item[2:]
            for item in group.get("rule", [])
            if isinstance(item, str) and item.startswith("[]")
        ]
        result.names.append(name)
    known = set(references) | BUILTIN_TARGETS
    for name, refs in references.items():
        for ref in refs:
            if ref not in known:
                result.diagnostics.append(
                    error(Code.GROUP_REFERENCE, f"组 {name!r} 引用了不存在的组 {ref!r}", span)
                )
    cycle = _find_cycle(references)
    if cycle:
        result.diagnostics.append(
            error(Code.GROUP_CYCLE, f"组之间存在循环引用：{' → '.join(cycle)}", span)
        )
    return result


def _check_group(name: str, group: dict[str, object], where: SourceSpan, out: GroupsResult) -> None:
    if any(ch in name for ch in ",\n\r") or name != name.strip():
        out.diagnostics.append(
            error(
                Code.GROUP_INVALID,
                f"组名 {name!r} 含逗号、换行或首尾空白，subconverter/Mihomo 无法无损表达",
                where,
            )
        )
    group_type = group.get("type")
    if group_type not in GROUP_TYPES:
        out.diagnostics.append(error(Code.GROUP_INVALID, f"组 {name!r} 的 type 无效", where))
    elif group_type in _NEEDS_PROBE and (
        not isinstance(group.get("url"), str) or not isinstance(group.get("interval"), int)
    ):
        out.diagnostics.append(
            error(Code.GROUP_INVALID, f"{group_type} 组 {name!r} 必须有 url 与 interval", where)
        )
    rules = group.get("rule")
    if rules is None and group.get("use") is None:
        out.diagnostics.append(error(Code.GROUP_INVALID, f"组 {name!r} 缺少 rule 或 use", where))
    if rules is not None and (
        not isinstance(rules, list) or not all(isinstance(r, str) for r in rules)
    ):
        out.diagnostics.append(
            error(Code.GROUP_INVALID, f"组 {name!r} 的 rule 必须是字符串数组", where)
        )
    elif isinstance(rules, list) and not rules and group.get("use") is None:
        out.diagnostics.append(warning(Code.GROUP_INVALID, f"组 {name!r} 的 rule 为空", where))


def _find_cycle(references: dict[str, list[str]]) -> list[str]:
    state: dict[str, int] = {}  # 0 未访问 / 1 访问中 / 2 完成
    path: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        path.append(node)
        for ref in references.get(node, []):
            if ref not in references:
                continue
            if state.get(ref, 0) == 1:
                return [*path[path.index(ref) :], ref]
            if state.get(ref, 0) == 0:
                found = visit(ref)
                if found:
                    return found
        path.pop()
        state[node] = 2
        return []

    for node in references:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return []


def is_known_target(name: str, groups: list[str]) -> bool:
    return name in BUILTIN_TARGETS or name in groups
