"""来源格式：名称登记、内容识别（format=auto）与分派。

识别规则见 docs/rules/merge-cases.md §3.2：只依据内容，URL 扩展名不参与；
同一内容可被多种格式以不同含义解释时报错，要求显式指定格式。
"""

from __future__ import annotations

import json
from collections.abc import Callable

from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.parse.formats.adguard import parse_adguard
from domainrouter_v2.parse.formats.base import (
    Entry,
    ParseResult,
    Skipped,
    SourceFormatError,
    iter_lines,
)
from domainrouter_v2.parse.formats.lists import (
    DNSMASQ_DIRECTIVES,
    parse_dnsmasq,
    parse_hosts,
    parse_surge_domainset,
)
from domainrouter_v2.parse.formats.mihomo import (
    Behavior,
    is_payload_yaml,
    parse_clash_config,
    parse_mihomo,
)
from domainrouter_v2.parse.formats.rulelist import parse_rulelist
from domainrouter_v2.parse.formats.singbox import parse_singbox
from domainrouter_v2.parse.rule_text import looks_like_rule

__all__ = [
    "FORMATS",
    "Entry",
    "ParseResult",
    "Skipped",
    "SourceFormatError",
    "detect_format",
    "parse_source",
]

Parser = Callable[[str], ParseResult]

FORMATS: dict[str, Parser] = {
    "mihomo": parse_mihomo,
    "domain": lambda text: parse_mihomo(text, Behavior.DOMAIN),
    "ipcidr": lambda text: parse_mihomo(text, Behavior.IPCIDR),
    "classical": lambda text: parse_mihomo(text, Behavior.CLASSICAL),
    "surge": lambda text: parse_rulelist(text, "surge"),
    "loon": lambda text: parse_rulelist(text, "loon"),
    "surge-domainset": parse_surge_domainset,
    "singbox": parse_singbox,
    "adguard": parse_adguard,
    "hosts": parse_hosts,
    "dnsmasq": parse_dnsmasq,
}
FORMAT_NAMES = frozenset({"auto", "wei", "clash-config", *FORMATS})

_MAJORITY = 0.5


def parse_source(text: str, fmt: str, exclude_types: tuple[str, ...] = ()) -> ParseResult:
    """按格式名解析来源文本。``wei`` 由文档解析器处理，不经过这里。"""
    if "\x00" in text:
        raise SourceFormatError("内容是二进制数据（如 .mrs/.srs/.dat），不是文本规则")
    if fmt == "clash-config":
        return parse_clash_config(text, exclude_types)
    if exclude_types:
        raise SourceFormatError("exclude_types 只适用于 format=clash-config")
    name = detect_format(text) if fmt == "auto" else fmt
    parser = FORMATS.get(name)
    if parser is None:
        raise SourceFormatError(f"未知格式 {fmt!r}")
    result = parser(text)
    if fmt == "auto":
        result.format = f"auto→{result.format}"
    return result


def detect_format(text: str) -> str:
    body = text.removeprefix("﻿").lstrip()
    if not body:
        raise SourceFormatError("内容为空")
    if body.startswith("{"):
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SourceFormatError(f"JSON 语法错误：{exc}") from exc
        if isinstance(data, dict) and "rules" in data and "version" in data:
            return "singbox"
        raise SourceFormatError("无法识别的 JSON 内容")
    if body.lstrip("-\n\r ").startswith("<") or "<html" in body[:2048].lower():
        raise SourceFormatError("内容是 HTML 页面，不是规则")
    if is_payload_yaml(text):
        return "mihomo"

    counts = {"dnsmasq": 0, "adguard": 0, "hosts": 0, "rule": 0, "plus": 0, "dot": 0, "plain": 0}
    meaningful = 0
    for _, line in iter_lines(text):
        if not line or line.startswith(("#", "//", ";")) or line == "---":
            continue
        if line.startswith("!"):
            counts["adguard"] += 1
            continue
        meaningful += 1
        if line.startswith(DNSMASQ_DIRECTIVES):
            counts["dnsmasq"] += 1
        elif line.startswith(("||", "|", "@@")) or line.endswith("^") or "^$" in line:
            counts["adguard"] += 1
        elif looks_like_rule(line.removeprefix("- ").strip("'\"")):
            counts["rule"] += 1
        elif _is_hosts_line(line):
            counts["hosts"] += 1
        elif line.startswith("+."):
            counts["plus"] += 1
        elif line.startswith("."):
            counts["dot"] += 1
        else:
            counts["plain"] += 1
    if meaningful == 0:
        raise SourceFormatError("没有任何规则行")
    if counts["dnsmasq"] and not counts["adguard"] and not counts["rule"]:
        return "dnsmasq"
    if counts["adguard"] and not counts["dnsmasq"] and not counts["rule"]:
        return "adguard"
    if counts["hosts"] >= meaningful * _MAJORITY and not counts["rule"]:
        return "hosts"
    if counts["rule"] >= meaningful * _MAJORITY:
        return "surge"
    if counts["rule"] or counts["hosts"]:
        raise SourceFormatError("规则行与其他内容混杂，请用 format= 显式指定格式")
    if counts["plus"]:
        return "mihomo"
    if counts["dot"]:
        raise SourceFormatError(
            "以 '.' 开头的域名在 Surge DOMAIN-SET 中包含自身、在 Mihomo 中不包含自身",
        )
    return "mihomo"


def _is_hosts_line(line: str) -> bool:
    fields = line.split("#", 1)[0].split()
    if len(fields) < 2 or "/" in fields[0]:
        return False
    try:
        parse_network(fields[0])
    except AddressError:
        return False
    return True
