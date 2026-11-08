"""``my.wei`` 文档解析：节、指令、粘贴块与 ``[Rules]``（规范 §4）。

逐行有状态解析，保留每个条目的原始位置。不会用跨文件正则按任意 ``[`` 切分。
解析只读原文，从不改写 ``my.wei``。
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from domainrouter_v2.diagnostics import Code, Diagnostic, SourceSpan, error, warning
from domainrouter_v2.model.domain import DomainError, DomainPattern, normalize_host
from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.model.profile import (
    Collection,
    LocalMember,
    Profile,
    RouteEntry,
    RouteKind,
    SourceRef,
)
from domainrouter_v2.model.rule import Leaf, Logic
from domainrouter_v2.parse.formats import FORMAT_NAMES, SourceFormatError, parse_source
from domainrouter_v2.parse.formats.base import ParseResult
from domainrouter_v2.parse.formats.common import add_rule
from domainrouter_v2.parse.formats.mihomo import parse_mihomo
from domainrouter_v2.parse.freeline import FreeLineError, convert_free_line
from domainrouter_v2.parse.rule_text import NoResolvePolicy, RuleProblem, convert_condition
from domainrouter_v2.parse.yaml_safe import YamlStructureError, load_list_document

RULES_SECTION = "Rules"
_SECTION = re.compile(r"^\[(?P<name>[^\[\]\x00-\x1f]+)\]\s*(?:(?:#|//|;).*)?$")
_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
_IMPLICIT_BLOCK = re.compile(r"^(?P<key>payload|rules)\s*:\s*(?:#.*)?$")
_COMMENT = ("#", ";", "//")
_ROUTE_PARAMS = frozenset({"no-resolve", "src"})


@dataclass(slots=True)
class ParsedProfile:
    profile: Profile
    diagnostics: list[Diagnostic] = field(default_factory=list)


def parse_profile(text: str, origin: str) -> ParsedProfile:
    parser = _Parser(origin)
    parser.run(text.removeprefix("﻿").splitlines())
    return ParsedProfile(parser.profile, parser.diagnostics)


class _Parser:
    def __init__(self, origin: str) -> None:
        self.origin = origin
        self.profile = Profile()
        self.diagnostics: list[Diagnostic] = []
        self.rules_lines: list[tuple[int, str]] = []
        self.seen_rules = False

    def span(self, line: int, text: str = "") -> SourceSpan:
        return SourceSpan(self.origin, line, text)

    # ---- 节与行分派 ----

    def run(self, lines: list[str]) -> None:
        current: Collection | None = None
        in_rules = False
        index = 0
        while index < len(lines):
            number, raw = index + 1, lines[index]
            stripped = raw.strip()
            header = _SECTION.match(raw)
            if header:
                current, in_rules = self._open_section(header.group("name"), number, raw)
                index += 1
                continue
            if not stripped or stripped.startswith(_COMMENT):
                index += 1
                continue
            if in_rules:
                self.rules_lines.append((number, stripped))
                index += 1
                continue
            if current is None:
                self.diagnostics.append(
                    error(Code.PARSE_SYNTAX, "内容出现在任何节之前", self.span(number, raw))
                )
                index += 1
                continue
            index = self._collection_line(current, lines, index)
        self._parse_rules()

    def _open_section(self, name: str, number: int, raw: str) -> tuple[Collection | None, bool]:
        if name == RULES_SECTION:
            if self.seen_rules:
                self.diagnostics.append(
                    error(Code.PARSE_SYNTAX, "重复的 [Rules] 节", self.span(number, raw))
                )
            self.seen_rules = True
            return None, True
        existing = self.profile.collections.get(name)
        if existing is not None:
            self.diagnostics.append(
                warning(
                    Code.DUPLICATE_SECTION,
                    f"合集 [{name}] 重复声明，按出现顺序合并成员",
                    self.span(number, raw),
                )
            )
            return existing, False
        collection = Collection(name, self.span(number, raw))
        self.profile.collections[name] = collection
        return collection, False

    def _collection_line(self, collection: Collection, lines: list[str], index: int) -> int:
        number, raw = index + 1, lines[index]
        stripped = raw.strip()
        block = _IMPLICIT_BLOCK.match(raw)
        if block:
            return self._implicit_block(collection, block.group("key"), lines, index)
        if stripped.startswith("@begin"):
            return self._explicit_block(collection, lines, index)
        if stripped == "@end":
            self.diagnostics.append(
                error(Code.PARSE_SYNTAX, "@end 没有对应的 @begin", self.span(number, raw))
            )
        elif stripped.startswith("@"):
            self._directive(collection, number, stripped)
        elif _URL.match(stripped):
            collection.items.append(SourceRef(stripped, "auto", self.span(number, stripped)))
        else:
            self._free_line(collection, number, stripped)
        return index + 1

    # ---- 自由行与指令 ----

    def _free_line(self, collection: Collection, number: int, text: str) -> None:
        try:
            result = convert_free_line(text)
        except FreeLineError as exc:
            code = Code.TARGET_UNSUPPORTED if exc.skip else Code.PARSE_AMBIGUOUS
            self.diagnostics.append(error(code, exc.message, self.span(number, text), exc.hint))
            return
        collection.items.append(
            LocalMember(result.member, self.span(number, text), tuple(result.notes))
        )

    def _directive(self, collection: Collection, number: int, text: str) -> None:
        span = self.span(number, text)
        try:
            tokens = shlex.split(text, posix=True)
        except ValueError as exc:
            self.diagnostics.append(error(Code.PARSE_SYNTAX, f"指令引号不配对：{exc}", span))
            return
        name, args = tokens[0], tokens[1:]
        if name == "@source":
            self._source(collection, span, args)
        elif name == "@site":
            self._site(collection, span, args)
        else:
            self.diagnostics.append(error(Code.PARSE_SYNTAX, f"未知指令 {name}", span))

    def _source(self, collection: Collection, span: SourceSpan, args: list[str]) -> None:
        if not args or not _URL.match(args[0]):
            self.diagnostics.append(error(Code.PARSE_SYNTAX, "@source 需要 http(s) URL", span))
            return
        options: dict[str, str] = {}
        for arg in args[1:]:
            key, sep, value = arg.partition("=")
            if not sep or key not in {"format", "exclude_types"} or key in options:
                self.diagnostics.append(error(Code.PARSE_SYNTAX, f"未知或重复的参数 {arg!r}", span))
                return
            options[key] = value
        fmt = options.get("format", "auto")
        if fmt not in FORMAT_NAMES:
            names = ", ".join(sorted(FORMAT_NAMES))
            self.diagnostics.append(
                error(Code.SOURCE_FORMAT, f"未知格式 {fmt!r}", span, f"可用格式：{names}")
            )
            return
        excluded = tuple(
            t.strip().upper() for t in options.get("exclude_types", "").split(",") if t
        )
        if excluded and (fmt != "clash-config" or not set(excluded) <= {"MATCH", "FINAL"}):
            self.diagnostics.append(
                error(
                    Code.PARSE_SYNTAX,
                    "exclude_types 只适用于 format=clash-config，且只能排除 MATCH、FINAL",
                    span,
                )
            )
            return
        collection.items.append(SourceRef(args[0], fmt, span, excluded))

    def _site(self, collection: Collection, span: SourceSpan, args: list[str]) -> None:
        if len(args) != 1:
            self.diagnostics.append(error(Code.PARSE_SYNTAX, "@site 需要且只需要一个 URL", span))
            return
        host = urlsplit(args[0] if "://" in args[0] else f"//{args[0]}").hostname
        if not host:
            self.diagnostics.append(error(Code.PARSE_SYNTAX, f"无法提取主机名：{args[0]!r}", span))
            return
        note = (f"@site 提取主机名 {host}",)
        try:
            network = parse_network(host).network
        except AddressError:
            pass
        else:
            collection.items.append(LocalMember(network, span, note))
            return
        try:
            pattern = DomainPattern.suffix(normalize_host(host.rstrip(".")))
        except DomainError as exc:
            self.diagnostics.append(error(Code.PARSE_AMBIGUOUS, str(exc), span))
            return
        collection.items.append(LocalMember(pattern, span, note))

    # ---- 粘贴块 ----

    def _implicit_block(
        self, collection: Collection, key: str, lines: list[str], index: int
    ) -> int:
        """行首 payload:/rules: 开始，吸收后续缩进行、空行与注释；回到列 0 的内容行结束。"""
        start = index
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line[0].isspace() and not line.lstrip().startswith("#"):
                break
            index += 1
        text = "\n".join(lines[start:index])
        self._absorb_block(collection, key, text, start + 1)
        return index

    def _explicit_block(self, collection: Collection, lines: list[str], index: int) -> int:
        number, raw = index + 1, lines[index].strip()
        span = self.span(number, raw)
        try:
            tokens = shlex.split(raw)
        except ValueError:
            tokens = []
        fmt = ""
        if len(tokens) == 2 and tokens[0] == "@begin" and tokens[1].startswith("format="):
            fmt = tokens[1].removeprefix("format=")
        if fmt not in FORMAT_NAMES or fmt == "clash-config":
            self.diagnostics.append(
                error(Code.PARSE_SYNTAX, "块必须写成 @begin format=<格式>", span)
            )
        end = index + 1
        while end < len(lines) and lines[end].strip() != "@end":
            end += 1
        if end >= len(lines):
            self.diagnostics.append(
                error(Code.PARSE_SYNTAX, "@begin 缺少对应的 @end", span, "请补上独立一行的 @end")
            )
            return end
        if fmt in FORMAT_NAMES and fmt != "clash-config":
            body = "\n".join(lines[index + 1 : end])
            if fmt == "wei":
                for offset, line in enumerate(lines[index + 1 : end], number + 1):
                    if line.strip() and not line.strip().startswith(_COMMENT):
                        self._free_line(collection, offset, line.strip())
            else:
                self._absorb_block(collection, fmt, body, number + 1)
        return end + 1

    def _absorb_block(self, collection: Collection, fmt: str, text: str, first_line: int) -> None:
        """first_line：隐式块为 payload:/rules: 所在行；显式块为内容的第一行。

        隐式块条目的行号按「键所在行 + 条目序号」近似（每项一行时准确）。
        """
        span = self.span(first_line)
        try:
            if fmt == "payload":
                result, offset = parse_mihomo(text), first_line
            elif fmt == "rules":
                result, offset = _parse_rules_block(text), first_line
            else:
                result, offset = parse_source(text, fmt), first_line - 1
        except SourceFormatError as exc:
            self.diagnostics.append(error(Code.YAML_STRUCTURE, str(exc), span))
            return
        for entry in result.entries:
            entry_span = self.span(offset + entry.line)
            collection.items.append(LocalMember(entry.member, entry_span, entry.notes))
        for skipped in result.skipped:
            self.diagnostics.append(
                warning(
                    Code.RULE_SKIPPED,
                    f"粘贴块条目未转换：{skipped.text}（{skipped.reason}）",
                    self.span(offset + skipped.line, skipped.text),
                )
            )

    # ---- [Rules] ----

    def _parse_rules(self) -> None:
        if not self.seen_rules:
            self.diagnostics.append(error(Code.ROUTE_FALLBACK, "缺少 [Rules] 节"))
            return
        for number, text in self.rules_lines:
            entry = self._route(len(self.profile.routes), number, text)
            if entry is not None:
                self.profile.routes.append(entry)
        matches = [r for r in self.profile.routes if r.kind is RouteKind.MATCH]
        if len(matches) != 1:
            self.diagnostics.append(
                error(Code.ROUTE_FALLBACK, f"[Rules] 必须恰好有一条 MATCH，实际 {len(matches)} 条")
            )
        elif self.profile.routes[-1].kind is not RouteKind.MATCH:
            self.diagnostics.append(
                error(Code.ROUTE_FALLBACK, "MATCH 必须是 [Rules] 的最后一条", matches[0].span)
            )

    def _route(self, index: int, number: int, text: str) -> RouteEntry | None:
        span = self.span(number, text)
        split = split_route(text)
        if split is None:
            left, sep, right = text.partition(":")
            if sep and left.strip() in self.profile.collections and right.strip():
                split = (left.strip(), right.strip())  # 历史写法 Example:DIRECT，分解唯一
            else:
                self.diagnostics.append(
                    error(Code.ROUTE_REFERENCE, "缺少「条件: 策略组」分隔符", span)
                )
                return None
        left, right = split
        fields = [f.strip() for f in right.split(",")]
        target, params = fields[0], fields[1:]
        if not target:
            self.diagnostics.append(error(Code.ROUTE_REFERENCE, "缺少目标策略组", span))
            return None
        if "," not in left:
            if left.upper() in {"MATCH", "FINAL"}:
                if not self._no_params(params, span):
                    return None
                return RouteEntry(index, RouteKind.MATCH, target, span)
            if left not in self.profile.collections:
                self.diagnostics.append(
                    error(Code.ROUTE_REFERENCE, f"引用了未定义的合集 {left!r}", span)
                )
                return None
            if not self._no_params(params, span):
                return None
            return RouteEntry(index, RouteKind.COLLECTION, target, span, collection=left)
        return self._inline(index, left, target, params, span)

    def _no_params(self, params: list[str], span: SourceSpan) -> bool:
        if params:
            self.diagnostics.append(
                error(
                    Code.ROUTE_REFERENCE,
                    f"合集引用和 MATCH 不接受参数：{', '.join(params)}",
                    span,
                    "目标 IP 的 no-resolve 由合集成员类型决定",
                )
            )
            return False
        return True

    def _inline(
        self, index: int, left: str, target: str, params: list[str], span: SourceSpan
    ) -> RouteEntry | None:
        unknown = [p for p in params if p.lower() not in _ROUTE_PARAMS]
        if unknown:
            self.diagnostics.append(
                error(Code.ROUTE_REFERENCE, f"内联规则含未知参数：{', '.join(unknown)}", span)
            )
            return None
        try:
            converted = convert_condition(",".join([left, *params]), NoResolvePolicy.KEEP)
        except RuleProblem as exc:
            self.diagnostics.append(error(Code.TARGET_UNSUPPORTED, exc.message, span, exc.hint))
            return None
        condition = converted.member
        assert isinstance(condition, Leaf | Logic)
        if isinstance(condition, Logic) or "," in condition.payload:
            self.diagnostics.append(
                error(
                    Code.BACKEND_LOSSY,
                    "subconverter 会用正则重排含逗号的内联规则，导致该规则损坏",
                    span,
                    "把它放进一个合集，通过合集引用使用",
                )
            )
            return None
        return RouteEntry(index, RouteKind.INLINE, target, span, condition=condition)


def split_route(text: str) -> tuple[str, str] | None:
    """在顶层的「冒号 + 空白」处切分条件与目标。

    跳过引号、括号、方括号（正则字符类）内的冒号与反斜杠转义，
    因此 IPv6、``(?:…)``、``[a: b]`` 中的冒号不会被误认为分隔符（规范 §4.5）。
    """
    depth = 0
    quote = ""
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in {"'", '"'}:
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == ":" and depth == 0 and index + 1 < len(text) and text[index + 1].isspace():
            left, right = text[:index].strip(), text[index + 1 :].strip()
            return (left, right) if left and right else None
    return None


def _parse_rules_block(text: str) -> ParseResult:
    """粘贴的 ``rules:`` 块：Clash 规则行，剥离出口；兜底与引用语句报告为跳过。"""
    try:
        document = load_list_document(text)
    except YamlStructureError as exc:
        raise SourceFormatError(str(exc)) from exc
    result = ParseResult("rules-block")
    for number, item in enumerate(document.get("rules", []), 1):
        add_rule(result, number, item)
    return result
