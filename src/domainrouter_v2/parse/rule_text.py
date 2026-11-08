"""解析一条 ``TYPE,值[,策略][,参数…]`` 形式的显式规则，转换为合集成员。

适用于 Surge / Loon / Mihomo classical 规则列表、``my.wei`` 中的显式规则行和内联规则。
只保留匹配条件：策略字段与附加参数全部剥离，但会改变含义的参数除外——
Mihomo 的 ``src`` 把目标地址条件变为来源地址条件，因此转换为对应的 ``SRC-*`` 类型。

字段切分遵守类型语法，而不是简单地按逗号截断：
- 逻辑规则的值是括号表达式，按括号深度定位结束位置；
- 正则类型的值可以含逗号：带引号时取引号内内容（Surge），否则只从右侧剥离已知参数。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from domainrouter_v2.model.domain import DomainError, DomainPattern, normalize_host
from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.model.rule import Condition, Leaf, Logic, Member
from domainrouter_v2.registry import (
    TYPES,
    UNSUPPORTED,
    Kind,
    canonical_type,
    is_known_param,
)

_REGEX_TYPES = frozenset({"DOMAIN-REGEX", "PROCESS-NAME-REGEX", "PROCESS-PATH-REGEX"})
_PORT_TYPES = frozenset({"DST-PORT", "SRC-PORT", "IN-PORT"})
MAX_PORT = 65535


class NoResolvePolicy(StrEnum):
    FORCE = "force"  # 合集成员与上游规则：目标 IP 条件一律 no-resolve
    KEEP = "keep"  # 手写内联规则：保留用户写的参数


class ProblemKind(StrEnum):
    SKIP = "skip"  # 合法但无法转换（MITM、无等价条件、控制语句等）
    INVALID = "invalid"  # 写法错误或语义无法唯一确定


class RuleProblem(Exception):
    def __init__(self, kind: ProblemKind, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.hint = hint


@dataclass(slots=True)
class Converted:
    member: Member
    notes: list[str] = field(default_factory=list)  # 修复与剥离说明，进入报告
    stripped: list[str] = field(default_factory=list)  # 被剥离的策略/参数字段原文


def looks_like_rule(text: str) -> bool:
    """首字段是登记过的（含不支持的）类型名时才视为显式规则行。"""
    head, sep, _ = text.partition(",")
    if not sep:
        return False
    name = canonical_type(head)
    return name in TYPES or name in UNSUPPORTED or name == "PROTOCOL"


def convert_rule(text: str, policy: NoResolvePolicy = NoResolvePolicy.FORCE) -> Converted:
    """把一条显式规则转换为成员。无法转换时抛 RuleProblem。"""
    result = Converted(member=Leaf("", ""))
    result.member = _convert(text.strip(), policy, result, top_level=True)
    return result


def convert_condition(text: str, policy: NoResolvePolicy = NoResolvePolicy.KEEP) -> Converted:
    """把规则转换为 classical 条件树（不拆入 domain/ipcidr 集合），用于 [Rules] 内联规则。"""
    result = Converted(member=Leaf("", ""))
    result.member = _convert(text.strip(), policy, result, top_level=False)
    return result


def _convert(text: str, policy: NoResolvePolicy, out: Converted, *, top_level: bool) -> Member:
    head, sep, rest = text.partition(",")
    if not sep:
        raise RuleProblem(ProblemKind.INVALID, f"不是 TYPE,值 形式的规则：{text!r}")
    name = canonical_type(head)
    if name in UNSUPPORTED:
        raise RuleProblem(ProblemKind.SKIP, f"{name}：{UNSUPPORTED[name]}")
    if name == "PROTOCOL":
        return _convert_protocol(rest, out)
    spec = TYPES.get(name)
    if spec is None:
        raise RuleProblem(ProblemKind.SKIP, f"未登记的规则类型 {head.strip()!r}")
    if spec.kind is Kind.CONTROL:
        raise RuleProblem(ProblemKind.SKIP, f"{name} 是控制/引用语句，不能作为合集成员")
    if spec.kind is Kind.LOGIC:
        return _convert_logic(name, rest, policy, out)

    payload, extras = _split_payload(name, rest)
    out.stripped.extend(e for e in extras if e)
    lowered = {e.strip().lower() for e in extras}
    if "src" in lowered:
        if spec.src_variant is None:
            raise RuleProblem(ProblemKind.INVALID, f"{name} 不接受 src 参数")
        name = spec.src_variant
        spec = TYPES[name]
        out.notes.append(f"src 参数表示来源地址，转换为 {name}")
    want_no_resolve = spec.target_ip and (
        policy is NoResolvePolicy.FORCE or "no-resolve" in lowered
    )
    params = ("no-resolve",) if want_no_resolve else ()
    return _convert_leaf(name, payload, params, out, top_level=top_level)


def _convert_protocol(rest: str, out: Converted) -> Member:
    value = rest.split(",", 1)[0].strip().upper()
    if value in {"TCP", "UDP"}:
        out.notes.append(f"PROTOCOL,{value} 转换为 NETWORK,{value}")
        return Leaf("NETWORK", value)
    raise RuleProblem(ProblemKind.SKIP, f"PROTOCOL,{value}：Mihomo 只能区分 TCP/UDP")


def _split_payload(name: str, rest: str) -> tuple[str, list[str]]:
    """返回 (值, 其余字段)。其余字段是策略或参数，全部由调用方剥离。"""
    stripped = rest.strip()
    if stripped[:1] in {'"', "'"}:
        quote = stripped[0]
        end = stripped.find(quote, 1)
        if end < 0:
            raise RuleProblem(ProblemKind.INVALID, f"引号不配对：{rest!r}")
        tail = stripped[end + 1 :].strip()
        if tail and not tail.startswith(","):
            raise RuleProblem(ProblemKind.INVALID, f"引号后有多余内容：{rest!r}")
        return stripped[1:end], [f.strip() for f in tail[1:].split(",")] if tail else []
    fields = [f.strip() for f in rest.split(",")]
    if name in _REGEX_TYPES:
        # 正则可能含逗号：只从右侧剥离可识别的参数，其余全部视为正则本身
        extras: list[str] = []
        while len(fields) > 1 and is_known_param(fields[-1]):
            extras.insert(0, fields.pop())
        return ",".join(fields), extras
    return fields[0], fields[1:]


def _convert_leaf(
    name: str, payload: str, params: tuple[str, ...], out: Converted, *, top_level: bool
) -> Member:
    if not payload:
        raise RuleProblem(ProblemKind.INVALID, f"{name} 缺少值")
    if name in {"DOMAIN", "DOMAIN-SUFFIX"}:
        return _domain_member(name, payload, out, top_level=top_level)
    if name in {"IP-CIDR", "IP-CIDR6", "SRC-IP-CIDR"}:
        try:
            parsed = parse_network(payload)
        except AddressError as exc:
            raise RuleProblem(ProblemKind.INVALID, str(exc)) from exc
        if parsed.host_bits_cleared:
            out.notes.append(f"网段 {payload} 含主机位，规范化为 {parsed.network}")
        if parsed.unmapped:
            out.notes.append(f"IPv4 映射地址 {payload} 还原为 {parsed.network}")
        if name == "SRC-IP-CIDR":
            return Leaf(name, str(parsed.network))
        if top_level:
            return parsed.network
        cidr_type = "IP-CIDR" if parsed.network.version == 4 else "IP-CIDR6"
        return Leaf(cidr_type, str(parsed.network), params)
    if name in {"IP-ASN", "SRC-IP-ASN"}:
        number = payload.upper().removeprefix("AS")
        if not number.isdigit():
            raise RuleProblem(ProblemKind.INVALID, f"ASN 必须是数字：{payload!r}")
        return Leaf(name, str(int(number)), params)
    if name == "DOMAIN-KEYWORD":
        return Leaf(name, payload.lower())
    if name == "NETWORK":
        value = payload.upper()
        if value not in {"TCP", "UDP"}:
            raise RuleProblem(ProblemKind.INVALID, f"NETWORK 只能是 TCP 或 UDP：{payload!r}")
        return Leaf(name, value)
    if name in _PORT_TYPES:
        return Leaf(name, normalize_ports(payload))
    return Leaf(name, payload, params)


def _domain_member(name: str, payload: str, out: Converted, *, top_level: bool) -> Member:
    host = payload
    if name == "DOMAIN-SUFFIX" and host.startswith(".") and not host.startswith(".."):
        host = host[1:]
        out.notes.append(
            f"DOMAIN-SUFFIX,{payload} 在 Mihomo 中永不命中，按作者意图修复为 {host} 的后缀"
        )
    if any(ch in host for ch in "*+?") or host.startswith("."):
        raise RuleProblem(
            ProblemKind.INVALID,
            f"{name} 的值是字面域名，不能含通配或前缀符号：{payload!r}",
            hint="通配请使用原生 domain 写法或 DOMAIN-WILDCARD",
        )
    if host.endswith(".") and not host.endswith(".."):
        host = host[:-1]
        out.notes.append(f"去除末尾根点：{payload}")
    try:
        host = normalize_host(host)
    except DomainError as exc:
        raise RuleProblem(ProblemKind.INVALID, str(exc), exc.hint) from exc
    if not payload.isascii():
        out.notes.append(f"国际化域名 {payload} 转换为 {host}")
    if not top_level:
        return Leaf(name, host)
    return DomainPattern.exact(host) if name == "DOMAIN" else DomainPattern.suffix(host)


def _convert_logic(op: str, rest: str, policy: NoResolvePolicy, out: Converted) -> Condition:
    expr = rest.lstrip()
    if not expr.startswith("("):
        raise RuleProblem(ProblemKind.INVALID, f"{op} 的值必须是括号表达式：{rest!r}")
    end = _matching_paren(expr, 0)
    tail = expr[end + 1 :].strip()
    if tail:
        if not tail.startswith(","):
            raise RuleProblem(ProblemKind.INVALID, f"{op} 表达式后有多余内容：{tail!r}")
        out.stripped.extend(f.strip() for f in tail[1:].split(",") if f.strip())
    children_text = _split_top_level_groups(expr[1:end])
    if not children_text:
        raise RuleProblem(ProblemKind.INVALID, f"{op} 没有子条件")
    if op == "NOT" and len(children_text) != 1:
        raise RuleProblem(ProblemKind.INVALID, "NOT 必须恰好有一个子条件")
    children: list[Condition] = []
    for child in children_text:
        try:
            member = _convert(child, policy, out, top_level=False)
        except RuleProblem as exc:
            # 删除任一子条件都会改变逻辑含义，只能整条放弃
            raise RuleProblem(exc.kind, f"{op} 的子条件无法转换（{exc.message}）") from exc
        assert isinstance(member, Leaf | Logic)
        children.append(member)
    return Logic(op, tuple(children))


def _matching_paren(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise RuleProblem(ProblemKind.INVALID, f"括号不配对：{text!r}")


def _split_top_level_groups(inner: str) -> list[str]:
    """``(A),(B,c)`` → ``["A", "B,c"]``。只接受由逗号分隔的顶层括号组。"""
    groups: list[str] = []
    index = 0
    while index < len(inner):
        while index < len(inner) and inner[index] in " ,":
            index += 1
        if index >= len(inner):
            break
        if inner[index] != "(":
            raise RuleProblem(ProblemKind.INVALID, f"逻辑子条件必须用括号包裹：{inner!r}")
        end = _matching_paren(inner, index)
        groups.append(inner[index + 1 : end].strip())
        index = end + 1
    return groups


def normalize_ports(text: str) -> str:
    """端口值规范化：支持单端口、``a-b`` 区间、``/`` 分隔的列表和 Surge 比较写法。"""
    parts: list[str] = []
    for raw in text.replace(" ", "").split("/"):
        token = raw
        for prefix, lo, hi in ((">=", 0, 0), ("<=", 0, 0), (">", 1, 0), ("<", 0, -1)):
            if token.startswith(prefix):
                number = _port(token[len(prefix) :])
                if prefix.startswith(">"):
                    parts.append(f"{number + lo}-{MAX_PORT}")
                else:
                    parts.append(f"0-{number + hi}")
                break
        else:
            if "-" in token or ":" in token:
                low, _, high = token.replace(":", "-").partition("-")
                a, b = _port(low), _port(high)
                if a > b:
                    raise RuleProblem(ProblemKind.INVALID, f"端口区间颠倒：{token!r}")
                parts.append(str(a) if a == b else f"{a}-{b}")
            else:
                parts.append(str(_port(token)))
    return "/".join(parts)


def _port(text: str) -> int:
    if not text.isdigit() or int(text) > MAX_PORT:
        raise RuleProblem(ProblemKind.INVALID, f"非法端口：{text!r}")
    return int(text)
