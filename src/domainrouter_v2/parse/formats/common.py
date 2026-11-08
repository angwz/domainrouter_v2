"""多个适配器共用的条目转换：原生域名条目、地址条目与规则行。"""

from __future__ import annotations

from domainrouter_v2.model.domain import DomainError, DomainPattern
from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.parse.formats.base import ParseResult
from domainrouter_v2.parse.rule_text import ProblemKind, RuleProblem, convert_rule


def add_native_domain(result: ParseResult, line: int, text: str) -> None:
    """Mihomo 原生域名条目（``.x`` 仅子域）。IP 字面量转入 ipcidr，末尾根点修复。"""
    notes: list[str] = []
    value = text
    if _is_address(value):
        add_address(result, line, value, note="IP 字面量在 domain 集合中永不命中，转入 ipcidr")
        return
    if value.endswith(".") and not value.endswith(".."):
        value = value[:-1]
        notes.append(f"去除末尾根点：{text}")
    if "/" in value:
        result.skip(line, text, "domain 条目不能含 '/'（内核会拒绝）", invalid=True)
        return
    try:
        pattern = DomainPattern.parse_native(value)
    except DomainError as exc:
        result.skip(line, text, str(exc), invalid=True)
        return
    if not value.isascii():
        notes.append(f"国际化域名 {text} 转换为 {pattern.to_native()}")
    result.add(pattern, line, notes)


def add_exact_or_suffix(result: ParseResult, line: int, host: str, *, suffix: bool) -> None:
    """其他格式中的字面主机名：转换为精确或后缀模式（不接受原生通配符）。"""
    if any(ch in host for ch in "*+?/") or host.startswith("."):
        result.skip(line, host, "不是字面域名", invalid=True)
        return
    if _is_address(host):
        add_address(result, line, host, note="IP 字面量出现在域名列表中，转入 ipcidr")
        return
    native = ("+." if suffix else "") + host
    add_native_domain(result, line, native)


def add_address(result: ParseResult, line: int, text: str, note: str = "") -> None:
    try:
        parsed = parse_network(text)
    except AddressError as exc:
        result.skip(line, text, str(exc), invalid=True)
        return
    notes = [note] if note else []
    if parsed.host_bits_cleared:
        notes.append(f"网段 {text} 含主机位，规范化为 {parsed.network}")
    if parsed.unmapped:
        notes.append(f"IPv4 映射地址 {text} 还原为 {parsed.network}")
    result.add(parsed.network, line, notes)


def add_rule(result: ParseResult, line: int, text: str) -> None:
    try:
        converted = convert_rule(text)
    except RuleProblem as exc:
        result.skip(line, text, exc.message, invalid=exc.kind is ProblemKind.INVALID)
        return
    result.add(converted.member, line, converted.notes)


def _is_address(text: str) -> bool:
    try:
        parse_network(text)
    except AddressError:
        return False
    return True
