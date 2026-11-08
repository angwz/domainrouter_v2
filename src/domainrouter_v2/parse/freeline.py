"""``my.wei`` 自由行语义：手写域名、地址与显式规则（规范 §4.2、§4.3、§4.6）。

与第三方格式最大的区别：未加单引号的域名默认包含全部子域（子域闭包）。
单引号只取消这一隐式扩展；双引号只是外围容器。显式规则行按其类型语义处理。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from domainrouter_v2.model.domain import DomainError, DomainPattern
from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.model.rule import Member
from domainrouter_v2.parse.rule_text import (
    NoResolvePolicy,
    ProblemKind,
    RuleProblem,
    convert_rule,
    looks_like_rule,
)

_LIST_MARKERS = ("- ", "* ", "• ", "+ ")
_PAIRED = {"'": "'", '"': '"', "‘": "’", "“": "”", "`": "`"}
_TRAILING_COMMENT = re.compile(r"\s+(#|//|;).*$")
_AMBIGUOUS_SYMBOLS = frozenset({"*", "+", "."})


class FreeLineError(Exception):
    def __init__(self, message: str, hint: str = "", *, skip: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.skip = skip  # 合法但无法转换（例如 USER-AGENT），区别于写法错误


@dataclass(slots=True)
class FreeLineResult:
    member: Member
    notes: list[str] = field(default_factory=list)


def convert_free_line(raw: str) -> FreeLineResult:
    """转换一条已去除首尾空白、非注释、非指令的自由行。"""
    notes: list[str] = []
    text = raw
    for marker in _LIST_MARKERS:
        if text.startswith(marker):
            text = text[len(marker) :].strip()
            notes.append(f"去除列表符号 {marker.strip()!r}")
            break
    if looks_like_rule(_unwrap_any(text)):
        return _explicit_rule(_unwrap_any(text), notes)
    text = _TRAILING_COMMENT.sub("", text)

    quote, inner = _unwrap(text)
    if quote == "`":
        notes.append("去除 Markdown 代码标记")
        quote, inner = _unwrap(inner)
    if quote in {"‘", "“"}:
        notes.append(f"中文引号 {quote} 规范化为{'单' if quote == '‘' else '双'}引号")
    single = quote in {"'", "‘"}

    try:
        parsed = parse_network(inner)
    except AddressError:
        pass
    else:
        if parsed.host_bits_cleared:
            notes.append(f"网段 {inner} 含主机位，规范化为 {parsed.network}")
        if parsed.unmapped:
            notes.append(f"IPv4 映射地址 {inner} 还原为 {parsed.network}")
        return FreeLineResult(parsed.network, notes)

    if inner in _AMBIGUOUS_SYMBOLS and not single:
        raise FreeLineError(
            f"孤立符号 {inner!r} 含义不明确",
            hint="全通配请写成单引号的原生模式，例如 '*' 或 '+.*'",
        )
    value = inner
    if value.endswith(".") and not value.endswith("..") and value not in _AMBIGUOUS_SYMBOLS:
        value = value[:-1]
        notes.append(f"去除末尾根点：{inner}")
    try:
        pattern = DomainPattern.parse_native(value)
    except DomainError as exc:
        raise FreeLineError(str(exc), exc.hint) from exc
    if not value.isascii():
        notes.append(f"国际化域名 {inner} 转换为 {pattern.to_native()}")
    if single:
        if pattern.literals == ():
            notes.append(f"{pattern.to_native()} 匹配所有域名，请确认这是有意的")
        return FreeLineResult(pattern, notes)
    return FreeLineResult(pattern.with_subdomain_closure(), notes)


def _explicit_rule(text: str, notes: list[str]) -> FreeLineResult:
    try:
        converted = convert_rule(text, NoResolvePolicy.FORCE)
    except RuleProblem as exc:
        raise FreeLineError(exc.message, exc.hint, skip=exc.kind is ProblemKind.SKIP) from exc
    return FreeLineResult(converted.member, notes + converted.notes)


def _unwrap(text: str) -> tuple[str, str]:
    """返回 (外围引号, 内容)；无引号时返回 ("", 原文)。不配对的引号报错。"""
    if not text:
        raise FreeLineError("空内容")
    opener = text[0]
    closer = _PAIRED.get(opener)
    if closer is None:
        if text[-1] in {"'", '"', "’", "”", "`"}:
            raise FreeLineError(f"引号不配对：{text!r}", hint="检查首尾引号是否成对")
        return "", text
    if len(text) < 2 or text[-1] != closer:
        raise FreeLineError(f"引号不配对：{text!r}", hint="检查首尾引号是否成对")
    inner = text[1:-1].strip()
    if not inner:
        raise FreeLineError("引号内为空")
    return opener, inner


def _unwrap_any(text: str) -> str:
    """显式规则行外围的成对引号/反引号只是包装。"""
    if len(text) >= 2 and _PAIRED.get(text[0]) == text[-1]:
        return text[1:-1].strip()
    return text
