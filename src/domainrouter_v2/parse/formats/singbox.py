"""sing-box 规则集 source 格式（JSON，version 1–5）。

依据：https://sing-box.sagernet.org/configuration/rule-set/source-format/
与 headless rule：https://sing-box.sagernet.org/configuration/rule-set/headless-rule/

一条 headless rule 的含义是：
``(domain ∨ domain_suffix ∨ domain_keyword ∨ domain_regex ∨ ip_cidr)
 ∧ (port ∨ port_range) ∧ (source_ip_cidr) ∧ (source_port ∨ source_port_range) ∧ 其他字段``。
只有域名/目标地址这一组时，它等价于若干独立成员的并集；
含其他字段时必须保留「与」关系，转换为 classical 的 AND 表达式，不能拆成并集。
``domain_suffix``：不带点的值含自身（1.9+），带点的值仅子域。
"""

from __future__ import annotations

import json
from typing import Any

from domainrouter_v2.model.domain import DomainError, DomainPattern
from domainrouter_v2.model.ip import AddressError, Network, parse_network
from domainrouter_v2.model.rule import Condition, Leaf, Logic, Member
from domainrouter_v2.parse.formats.base import ParseResult, SourceFormatError
from domainrouter_v2.parse.rule_text import RuleProblem, normalize_ports

MAX_VERSION = 5
_MATCH_FIELDS = ("domain", "domain_suffix", "domain_keyword", "domain_regex", "ip_cidr")
_OTHER_FIELDS = {
    "port": "DST-PORT",
    "port_range": "DST-PORT",
    "source_port": "SRC-PORT",
    "source_port_range": "SRC-PORT",
    "source_ip_cidr": "SRC-IP-CIDR",
    "network": "NETWORK",
    "process_name": "PROCESS-NAME",
    "process_path": "PROCESS-PATH",
    "process_path_regex": "PROCESS-PATH-REGEX",
    "package_name": "PROCESS-NAME",
}
# 同一组内为「或」关系的字段
_GROUPS = (
    ("port", "port_range"),
    ("source_port", "source_port_range"),
    ("source_ip_cidr",),
    ("network",),
    ("process_name", "process_path", "process_path_regex", "package_name"),
)

type Expr = list[Member] | Condition


class _Unsupported(Exception):
    pass


def parse_singbox(text: str) -> ParseResult:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceFormatError(f"JSON 语法错误：{exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
        raise SourceFormatError("sing-box 规则集必须是含 rules 数组的对象")
    version = data.get("version")
    if not isinstance(version, int) or not 1 <= version <= MAX_VERSION:
        raise SourceFormatError(f"不支持的 sing-box 规则集版本：{version!r}")
    result = ParseResult(f"singbox-v{version}")
    for index, rule in enumerate(data["rules"], 1):
        raw = json.dumps(rule, ensure_ascii=False, sort_keys=True)
        try:
            expr = _rule(rule)
        except _Unsupported as exc:
            result.skip(index, raw, str(exc))
            continue
        except (DomainError, AddressError, RuleProblem) as exc:
            result.skip(index, raw, str(exc), invalid=True)
            continue
        for member in expr if isinstance(expr, list) else [expr]:
            result.add(member, index)
    return result


def _rule(rule: Any) -> Expr:
    if not isinstance(rule, dict):
        raise _Unsupported("规则必须是对象")
    invert = bool(rule.get("invert", False))
    if rule.get("type") == "logical":
        mode = rule.get("mode")
        subs = rule.get("rules")
        if mode not in {"and", "or"} or not isinstance(subs, list) or not subs:
            raise _Unsupported("logical 规则需要 mode 为 and/or 且 rules 非空")
        exprs = [_rule(sub) for sub in subs]
        if mode == "or" and not invert and all(isinstance(e, list) for e in exprs):
            return [m for e in exprs if isinstance(e, list) for m in e]
        node: Condition = Logic(mode.upper(), tuple(_condition(e) for e in exprs))
        return Logic("NOT", (node,)) if invert else node
    unknown = set(rule) - set(_MATCH_FIELDS) - set(_OTHER_FIELDS) - {"invert", "type"}
    if unknown:
        raise _Unsupported(f"含 Mihomo 无等价条件的字段：{', '.join(sorted(unknown))}")
    match_group = [m for name in _MATCH_FIELDS for m in _match_members(name, rule.get(name))]
    groups: list[Expr] = [match_group] if match_group else []
    for names in _GROUPS:
        leaves = [leaf for name in names for leaf in _other_leaves(name, rule.get(name))]
        if leaves:
            groups.append(leaves[0] if len(leaves) == 1 else Logic("OR", tuple(leaves)))
    if not groups:
        raise _Unsupported("空规则")
    if len(groups) == 1 and not invert:
        return groups[0]
    if len(groups) == 1:
        node = _condition(groups[0])
    else:
        node = Logic("AND", tuple(_condition(g) for g in groups))
    return Logic("NOT", (node,)) if invert else node


def _values(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _match_members(name: str, value: Any) -> list[Member]:
    members: list[Member] = []
    for item in _values(value):
        text = str(item)
        if name == "domain":
            if any(ch in text for ch in "*+") or text.startswith("."):
                raise DomainError(f"domain 字段是字面域名：{text!r}")
            members.append(DomainPattern.parse_native(text.removesuffix(".")))
        elif name == "domain_suffix":
            if text.startswith("."):
                members.append(DomainPattern.parse_native("." + text[1:]))
            else:
                members.append(DomainPattern.parse_native("+." + text))
        elif name == "domain_keyword":
            members.append(Leaf("DOMAIN-KEYWORD", text.lower()))
        elif name == "domain_regex":
            members.append(Leaf("DOMAIN-REGEX", text))
        else:
            members.append(parse_network(text).network)
    return members


def _other_leaves(name: str, value: Any) -> list[Leaf]:
    rule_type = _OTHER_FIELDS[name]
    leaves: list[Leaf] = []
    for item in _values(value):
        text = str(item)
        if name in {"port", "source_port"}:
            leaves.append(Leaf(rule_type, normalize_ports(text)))
        elif name in {"port_range", "source_port_range"}:
            low, _, high = text.partition(":")
            leaves.append(Leaf(rule_type, normalize_ports(f"{low or 0}-{high or 65535}")))
        elif name == "source_ip_cidr":
            leaves.append(Leaf(rule_type, str(parse_network(text).network)))
        elif name == "network":
            if text.lower() not in {"tcp", "udp"}:
                raise _Unsupported(f"network {text!r} 无等价条件")
            leaves.append(Leaf(rule_type, text.upper()))
        else:
            leaves.append(Leaf(rule_type, text))
    return leaves


def _condition(expr: Expr) -> Condition:
    if not isinstance(expr, list):
        return expr
    leaves = [_leaf(member) for member in expr]
    return leaves[0] if len(leaves) == 1 else Logic("OR", tuple(leaves))


def _leaf(member: Member) -> Condition:
    if isinstance(member, Network):
        cidr_type = "IP-CIDR" if member.version == 4 else "IP-CIDR6"
        return Leaf(cidr_type, str(member), ("no-resolve",))
    if isinstance(member, DomainPattern):
        native = member.to_native()
        if "*" in native or native.startswith("."):
            raise _Unsupported(f"{native} 无法放进逻辑表达式（没有等价的单条规则）")
        if native.startswith("+."):
            return Leaf("DOMAIN-SUFFIX", native[2:])
        return Leaf("DOMAIN", native)
    return member
