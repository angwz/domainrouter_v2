"""my.wei 的无损编辑：文档大纲与行级编辑操作。

可视化编辑器（网页，经 Pyodide 运行本模块）与命令行共用这一份实现。

**无损**是第一约束：每个操作只改动它涉及的行，其余行逐字节保留，包括注释、空行、
缩进、行尾空白、换行风格（LF/CRLF）、文件末尾是否有换行以及 BOM。

结构识别复用 ``parse/document.py`` 的词法边界函数（节标题、注释、粘贴块的起止），
条目语义复用 ``parse_profile``，因此编辑器看到的结构与构建时完全一致。

单位（Unit）是编辑的最小对象：一行普通条目、一个粘贴块，或 ``[Rules]`` 中的一条路由。
紧贴在单位上方、中间没有空行的注释属于该单位，移动单位时随之移动；删除单位时保留，
以免误删描述后续几行的分组注释（如 ``# DMIT`` 下面的多个网段）。
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from domainrouter_v2.diagnostics import Diagnostic
from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.profile import LocalMember, RouteKind, SourceRef
from domainrouter_v2.model.rule import Logic, Member, render_member
from domainrouter_v2.parse.document import (
    RULES_SECTION,
    explicit_block_end,
    implicit_block_end,
    implicit_block_key,
    is_blank_or_comment,
    parse_profile,
    section_header,
    split_route,
)

_BOM = "﻿"
# str.splitlines 认作换行、但编辑后无法原样还原的字符。出现时拒绝编辑，而不是悄悄改写。
_EXOTIC_BREAKS = ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " ")


class EditError(ValueError):
    """操作无法执行；文本保持不变。"""


# ---- 大纲 ----


@dataclass(frozen=True, slots=True)
class Item:
    """单位解析出的一个成员，供界面展示。"""

    kind: str  # domain / network / rule / source
    text: str  # 规范化后的写法，例如 +.a.hk
    label: str  # 中文语义，例如「自身及全部子域」
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Route:
    kind: str  # collection / inline / match
    condition: str  # 合集名、内联条件或 MATCH
    target: str


@dataclass(frozen=True, slots=True)
class Unit:
    kind: str  # line / block / route
    first: int  # 首行行号（含紧贴上方的注释），从 1 开始
    line: int  # 主行行号：编辑操作用它指定单位
    last: int  # 末行行号（块为 @end 或最后一个缩进行）
    text: str  # 主行原文（去掉首尾空白）
    items: tuple[Item, ...] = ()
    route: Route | None = None
    problems: tuple[str, ...] = ()


@dataclass(slots=True)
class Section:
    name: str  # 前言（第一个节标题之前）为空串
    header: int  # 标题行号；前言为 0
    end: int  # 本节最后一行行号（下一个节标题之前）
    units: list[Unit] = field(default_factory=list)

    @property
    def is_rules(self) -> bool:
        return self.name == RULES_SECTION


@dataclass(slots=True)
class Outline:
    sections: list[Section]
    problems: list[str]  # 无法定位到具体行的诊断

    def section(self, name: str) -> Section:
        matches = [s for s in self.sections if s.name == name and s.header]
        if not matches:
            raise EditError(f"没有名为 [{name}] 的节")
        if len(matches) > 1:
            raise EditError(f"[{name}] 声明了多次，请先在原文模式中合并")
        return matches[0]

    def unit_at(self, line: int) -> tuple[Section, Unit]:
        for section in self.sections:
            for unit in section.units:
                if unit.line == line:
                    return section, unit
        raise EditError(f"第 {line} 行不是一个可编辑的条目")


def outline(text: str) -> Outline:
    doc = _Document.load(text)
    parsed = parse_profile(text, "my.wei")
    items, routes, problems = _index_parse(parsed.profile, parsed.diagnostics)
    sections: list[Section] = [Section("", 0, 0)]
    lines = doc.lines
    index = 0
    while index < len(lines):
        raw = lines[index]
        name = section_header(raw)
        if name is not None:
            sections[-1].end = index
            sections.append(Section(name, index + 1, index + 1))
            index += 1
            continue
        if is_blank_or_comment(raw):
            index += 1
            continue
        section = sections[-1]
        end = _unit_end(lines, index, in_rules=section.is_rules)
        first = _comment_start(lines, index)
        number, last = index + 1, end
        unit_items = tuple(item for n in range(number, last + 1) for item in items.get(n, ()))
        unit_problems = tuple(p for n in range(number, last + 1) for p in problems.get(n, ()))
        kind = "route" if section.is_rules else ("block" if last > number else "line")
        section.units.append(
            Unit(
                kind,
                first,
                number,
                last,
                raw.strip(),
                unit_items,
                routes.get(number),
                unit_problems,
            )
        )
        index = end
    sections[-1].end = len(lines)
    if not sections[0].units and sections[0].end == 0:
        sections.pop(0)
    return Outline(sections, problems.get(0, []))


def _unit_end(lines: list[str], index: int, *, in_rules: bool) -> int:
    """单位之后第一行的下标（也就是单位末行的行号）。"""
    if in_rules:
        return index + 1
    if implicit_block_key(lines[index]) is not None:
        end = implicit_block_end(lines, index)
        while end > index + 1 and is_blank_or_comment(lines[end - 1]):
            end -= 1  # 块尾的空行与注释不算块的一部分，留给后面的单位
        return end
    if lines[index].strip().startswith("@begin"):
        found = explicit_block_end(lines, index)
        return len(lines) if found is None else found + 1
    return index + 1


def _comment_start(lines: list[str], index: int) -> int:
    """紧贴在 index 行上方、中间没有空行的注释行，算作该单位的开头。"""
    first = index
    while first > 0:
        above = lines[first - 1]
        if not above.strip() or not is_blank_or_comment(above) or section_header(above):
            break
        first -= 1
    return first + 1


def _index_parse(
    profile: Any, diagnostics: list[Diagnostic]
) -> tuple[dict[int, list[Item]], dict[int, Route], dict[int, list[str]]]:
    items: dict[int, list[Item]] = {}
    for collection in profile.collections.values():
        for entry in collection.items:
            items.setdefault(entry.span.line, []).append(describe_entry(entry))
    routes: dict[int, Route] = {}
    for route in profile.routes:
        if route.kind is RouteKind.COLLECTION:
            condition = route.collection
        elif route.kind is RouteKind.MATCH:
            condition = "MATCH"
        else:
            condition = route.inline_text
        routes[route.span.line] = Route(route.kind.value, condition, route.target)
    problems: dict[int, list[str]] = {}
    for diagnostic in diagnostics:
        line = diagnostic.span.line if diagnostic.span else 0
        hint = f"（{diagnostic.hint}）" if diagnostic.hint else ""
        problems.setdefault(line, []).append(
            f"{diagnostic.level.value}: {diagnostic.message}{hint}"
        )
    return items, routes, problems


# ---- 单条语义 ----


def describe_entry(entry: LocalMember | SourceRef) -> Item:
    if isinstance(entry, SourceRef):
        label = "上游来源" + ("" if entry.format == "auto" else f" · {entry.format}")
        return Item("source", entry.url, label)
    return _describe_member(entry.member, entry.notes)


def _describe_member(member: Member, notes: tuple[str, ...] = ()) -> Item:
    text = render_member(member)
    if isinstance(member, DomainPattern):
        if member.max_labels == member.min_labels == len(member.literals):
            label = "仅自身"
        elif member.max_labels is None and member.min_labels == member.fixed_length:
            label = "自身及全部子域"
        elif member.max_labels is None:
            label = "全部子域，不含自身"
        else:
            label = "通配，固定层级"
        return Item("domain", text, label, notes)
    if isinstance(member, Network):
        return Item("network", text, f"IPv{member.version} 网段", notes)
    kind = member.op if isinstance(member, Logic) else member.type
    return Item("rule", text, f"{kind} 规则", notes)


def describe_line(line: str, *, section: str = "") -> tuple[list[Item], list[str]]:
    """输入框中的单行预览：放进一个临时合集（或 [Rules]）解析，返回成员与问题。"""
    stripped = line.strip()
    if not stripped:
        return [], []
    if section == RULES_SECTION:
        split = split_route(stripped)
        if split is None:
            return [], ["缺少「条件: 策略组」分隔符（冒号后需要空格）"]
        return [Item("route", split[0], f"→ {split[1]}")], []
    probe = f"[预览]\n{stripped}\n[Rules]\nMATCH: DIRECT\n"
    parsed = parse_profile(probe, "预览")
    entries = parsed.profile.collections["预览"].items
    problems = [
        d.message + (f"（{d.hint}）" if d.hint else "")
        for d in parsed.diagnostics
        if d.span is not None and d.span.line == 2
    ]
    return [describe_entry(entry) for entry in entries], problems


# ---- 文本模型 ----


@dataclass(slots=True)
class _Document:
    lines: list[str]
    newline: str
    trailing: bool
    bom: bool

    @classmethod
    def load(cls, text: str) -> _Document:
        if any(ch in text for ch in _EXOTIC_BREAKS):
            raise EditError("文件含有不常见的换行字符，请先在原文模式中清理")
        bom = text.startswith(_BOM)
        body = text.removeprefix(_BOM)
        newline = "\r\n" if "\r\n" in body else "\n"
        if "\r" in body.replace("\r\n", ""):
            raise EditError("文件混用了不同的换行风格，请先统一")
        return cls(body.splitlines(), newline, body.endswith(("\n", "\r")), bom)

    def dump(self) -> str:
        body = self.newline.join(self.lines) + (self.newline if self.trailing else "")
        return (_BOM if self.bom else "") + body


def _single_line(text: str) -> str:
    if "\n" in text or "\r" in text:
        raise EditError("条目只能是一行")
    if not text.strip():
        raise EditError("条目不能为空")
    if section_header(text) is not None:
        raise EditError("条目不能是节标题")
    return text


# ---- 编辑操作 ----


def add_line(text: str, section: str, line_text: str, *, after: int | None = None) -> str:
    """在节中加入一行。默认放在该节最后一个条目之后；[Rules] 中默认放在 MATCH 之前。"""
    new = _single_line(line_text.strip())
    doc, tree = _Document.load(text), outline(text)
    target = tree.section(section)
    if after is not None:
        _, unit = tree.unit_at(after)
        if not target.header < unit.line <= target.end:
            raise EditError(f"第 {after} 行不在 [{section}] 中")
        position = unit.last
    elif target.is_rules and target.units and _is_match(target.units[-1]):
        position = target.units[-1].first - 1
    elif target.units:
        position = target.units[-1].last
    else:
        position = target.header
    doc.lines.insert(position, new)
    return doc.dump()


def replace_line(text: str, line: int, line_text: str) -> str:
    """替换单行条目，保留原有缩进。"""
    new = _single_line(line_text.strip())
    doc, tree = _Document.load(text), outline(text)
    _, unit = tree.unit_at(line)
    if unit.last != unit.line:
        raise EditError("粘贴块请在原文模式中修改")
    original = doc.lines[line - 1]
    indent = original[: len(original) - len(original.lstrip())]
    doc.lines[line - 1] = indent + new
    return doc.dump()


def delete_unit(text: str, line: int) -> str:
    """删除一个单位（单行或整个粘贴块）。上方的注释保留，见模块说明。"""
    doc, tree = _Document.load(text), outline(text)
    _, unit = tree.unit_at(line)
    del doc.lines[unit.line - 1 : unit.last]
    return doc.dump()


def add_section(text: str, name: str) -> str:
    """新建合集：放在 [Rules] 之前，与前一节之间空一行。"""
    _check_name(name)
    doc, tree = _Document.load(text), outline(text)
    if any(s.name == name for s in tree.sections):
        raise EditError(f"[{name}] 已存在")
    rules = [s for s in tree.sections if s.is_rules]
    if rules:
        position = rules[0].header - 1
        while position > 0 and not doc.lines[position - 1].strip():
            position -= 1  # 插在上一节内容之后、空行之前，保持原有的节间空行
        doc.lines[position:position] = ["", f"[{name}]"]
    else:
        doc.lines += ["", f"[{name}]"] if doc.lines else [f"[{name}]"]
        doc.trailing = True
    return doc.dump()


def rename_section(text: str, name: str, new_name: str) -> str:
    """重命名合集，并同步修改 [Rules] 中引用它的路由。"""
    _check_name(new_name)
    if name == RULES_SECTION:
        raise EditError("[Rules] 不能重命名")
    doc, tree = _Document.load(text), outline(text)
    section = tree.section(name)
    if any(s.name == new_name for s in tree.sections):
        raise EditError(f"[{new_name}] 已存在")
    header = doc.lines[section.header - 1]
    doc.lines[section.header - 1] = header.replace(f"[{name}]", f"[{new_name}]", 1)
    for unit in _route_units(tree):
        if (
            unit.route is not None
            and unit.route.kind == "collection"
            and unit.route.condition == name
        ):
            raw = doc.lines[unit.line - 1]
            start = raw.index(name)
            doc.lines[unit.line - 1] = raw[:start] + new_name + raw[start + len(name) :]
    return doc.dump()


def delete_section(text: str, name: str) -> str:
    """删除合集及其全部内容。仍被 [Rules] 引用时拒绝，请先删除对应路由。"""
    if name == RULES_SECTION:
        raise EditError("[Rules] 不能删除")
    doc, tree = _Document.load(text), outline(text)
    section = tree.section(name)
    if any(u.route and u.route.condition == name for u in _route_units(tree)):
        raise EditError(f"[{name}] 仍被 [Rules] 引用，请先删除对应的路由")
    del doc.lines[section.header - 1 : section.end]
    return doc.dump()


def reorder_routes(text: str, order: Sequence[int]) -> str:
    """按 order（各路由主行行号的新顺序）重排 [Rules]。

    每条路由连同紧贴其上的注释一起移动；路由之间的空行与独立注释留在原位。
    """
    doc, tree = _Document.load(text), outline(text)
    units = _route_units(tree)
    by_line = {u.line: u for u in units}
    if sorted(order) != sorted(by_line) or len(order) != len(by_line):
        raise EditError("新顺序必须恰好包含 [Rules] 中的每一条路由")
    if not units:
        return text
    chunks = [doc.lines[u.first - 1 : u.last] for u in units]
    gaps = [doc.lines[a.last : b.first - 1] for a, b in itertools.pairwise(units)]
    moved = [doc.lines[by_line[n].first - 1 : by_line[n].last] for n in order]
    rebuilt: list[str] = []
    for i, chunk in enumerate(moved):
        rebuilt += chunk
        if i < len(gaps):
            rebuilt += gaps[i]
    assert sum(map(len, chunks)) + sum(map(len, gaps)) == len(rebuilt)
    doc.lines[units[0].first - 1 : units[-1].last] = rebuilt
    return doc.dump()


def apply(text: str, op: dict[str, Any]) -> str:
    """供网页调用的统一入口：``{"op": "add_line", ...}``。"""
    name = op.get("op")
    args = {k: v for k, v in op.items() if k != "op"}
    handlers = {
        "add_line": add_line,
        "replace_line": replace_line,
        "delete_unit": delete_unit,
        "add_section": add_section,
        "rename_section": rename_section,
        "delete_section": delete_section,
        "reorder_routes": reorder_routes,
    }
    handler = handlers.get(str(name))
    if handler is None:
        raise EditError(f"未知操作 {name!r}")
    try:
        result: str = handler(text, **args)  # type: ignore[operator]
    except TypeError as exc:
        raise EditError(f"操作参数不正确：{exc}") from exc
    return result


def _route_units(tree: Outline) -> list[Unit]:
    return [u for s in tree.sections if s.is_rules for u in s.units]


def _is_match(unit: Unit) -> bool:
    return unit.route is not None and unit.route.kind == "match"


def _check_name(name: str) -> None:
    if not name or name != name.strip() or section_header(f"[{name}]") != name:
        raise EditError(f"合集名不合法：{name!r}")
    if name == RULES_SECTION:
        raise EditError("Rules 是保留名")
