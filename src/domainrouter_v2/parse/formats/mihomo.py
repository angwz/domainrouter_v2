"""Mihomo rule-provider 内容（yaml 的 ``payload:`` 或 text 逐行）。

依据：https://wiki.metacubex.one/en/config/rule-providers/content/
- domain：原生域名模式（``.x`` 仅子域、``+.x`` 含自身、``*`` 单标签）；
- ipcidr：地址或网段；
- classical：不带策略的规则行。
text 格式以 ``#``、``//`` 开头的行为注释（mihomo rules/provider/provider.go）。
"""

from __future__ import annotations

from enum import StrEnum

from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.parse.formats.base import ParseResult, SourceFormatError, iter_lines
from domainrouter_v2.parse.formats.common import add_address, add_native_domain, add_rule
from domainrouter_v2.parse.rule_text import looks_like_rule
from domainrouter_v2.parse.yaml_safe import YamlStructureError, load_list_document


class Behavior(StrEnum):
    DOMAIN = "domain"
    IPCIDR = "ipcidr"
    CLASSICAL = "classical"


def is_payload_yaml(text: str) -> bool:
    for _, line in iter_lines(text):
        if not line or line.startswith("#") or line == "---":
            continue
        return line.startswith(("payload:", "payload :"))
    return False


def parse_mihomo(text: str, behavior: Behavior | None = None) -> ParseResult:
    """解析 Mihomo 内容；behavior 为 None 时按条目自动判断（merge-cases §3.3）。"""
    if is_payload_yaml(text):
        try:
            document = load_list_document(text)
        except YamlStructureError as exc:
            raise SourceFormatError(str(exc)) from exc
        if "payload" not in document:
            raise SourceFormatError("YAML 中没有 payload 键")
        items = list(enumerate(document["payload"], 1))
        name = "mihomo-yaml"
    else:
        items = [
            (number, line)
            for number, line in iter_lines(text)
            if line and not line.startswith(("#", "//"))
        ]
        name = "mihomo-text"
    result = ParseResult(f"{name}/{behavior or 'auto'}")
    for number, raw in items:
        item = raw.strip()
        kind = behavior or _guess(item)
        if kind is Behavior.CLASSICAL:
            add_rule(result, number, item)
        elif kind is Behavior.IPCIDR:
            add_address(result, number, item)
        else:
            add_native_domain(result, number, item)
    return result


def _guess(item: str) -> Behavior:
    if looks_like_rule(item):
        return Behavior.CLASSICAL
    try:
        parse_network(item)
    except AddressError:
        return Behavior.DOMAIN
    return Behavior.IPCIDR


EXCLUDABLE_TYPES = frozenset({"MATCH", "FINAL"})


def parse_clash_config(text: str, exclude_types: tuple[str, ...] = ()) -> ParseResult:
    """完整 Clash/Mihomo 配置：只提取 ``rules:`` 中的匹配条件，剥离出口（规范 §5）。

    兜底语句 MATCH/FINAL 必须由 ``exclude_types`` 显式排除，否则整份来源报错；
    ``RULE-SET``/``SUB-RULE`` 引用无法在此展开，同样报错。节点等其他字段不读取。
    """
    try:
        document = load_list_document(text, frozenset({"rules"}))
    except YamlStructureError as exc:
        raise SourceFormatError(str(exc)) from exc
    if "rules" not in document:
        raise SourceFormatError("完整配置中没有 rules 列表")
    excluded = {t.upper() for t in exclude_types}
    result = ParseResult("clash-config")
    for number, raw in enumerate(document["rules"], 1):
        item = raw.strip()
        head = item.split(",", 1)[0].strip().upper()
        if head in {"MATCH", "FINAL"}:
            if head not in excluded:
                raise SourceFormatError(
                    f"rules 第 {number} 条是兜底语句 {head}；"
                    "请用 exclude_types=MATCH,FINAL 显式排除"
                )
            result.skip(number, item, f"按 exclude_types 排除 {head}")
            continue
        if head in {"RULE-SET", "SUB-RULE"}:
            raise SourceFormatError(f"rules 第 {number} 条引用了 {head}，首版不展开嵌套引用")
        add_rule(result, number, item)
    return result
