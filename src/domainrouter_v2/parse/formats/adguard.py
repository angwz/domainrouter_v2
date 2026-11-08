"""AdGuard DNS 过滤语法中可转换为「正向域名集合」的子集。

依据：https://adguard-dns.io/kb/general/dns-filtering-syntax/
- ``||x^`` x 及全部子域；``|x^`` 仅 x；纯 ``x`` 行仅 x（不含子域）；hosts 风格行仅该主机名；
- ``!`` 与 ``#`` 开头为注释；
- 含文档未列出修饰符的规则「必须整条忽略」；
- ``$badfilter`` 使与之相同（去掉 badfilter 后）的规则失效；
- ``@@`` 例外规则无法用正向集合表达：只抵消同来源中完全相同的条目，其余跳过并说明。
"""

from __future__ import annotations

from domainrouter_v2.model.domain import DomainError, DomainPattern
from domainrouter_v2.model.ip import AddressError, parse_network
from domainrouter_v2.parse.formats.base import ParseResult, iter_lines
from domainrouter_v2.parse.formats.common import add_exact_or_suffix
from domainrouter_v2.parse.formats.lists import HOSTS_LOCAL_NAMES

DOCUMENTED_MODIFIERS = frozenset(
    {"important", "badfilter", "client", "ctag", "denyallow", "dnstype", "dnsrewrite"}
)
CONDITIONAL_MODIFIERS = frozenset({"client", "ctag", "denyallow", "dnstype", "dnsrewrite"})


def parse_adguard(text: str) -> ParseResult:
    result = ParseResult("adguard")
    exceptions: list[tuple[int, str, DomainPattern]] = []
    badfilters: list[tuple[int, str, DomainPattern]] = []
    for number, line in iter_lines(text):
        if not line or (line.startswith(("!", "#")) and not line.startswith("##")):
            continue
        if "##" in line or "#@#" in line or "#$#" in line or "#%#" in line:
            result.skip(number, line, "元素隐藏/脚本规则只作用于网页，不是域名条件")
            continue
        if _is_hosts_line(line):
            for name in line.split("#", 1)[0].split()[1:]:
                if name.lower() not in HOSTS_LOCAL_NAMES:
                    add_exact_or_suffix(result, number, name, suffix=False)
            continue
        exception = line.startswith("@@")
        body = line[2:] if exception else line
        pattern_text, modifiers, problem = _split_modifiers(body)
        if problem:
            result.skip(number, line, problem)
            continue
        if "badfilter" in modifiers and len(modifiers) > 1:
            result.skip(number, line, "带其他修饰符的 $badfilter 无法精确对应")
            continue
        pattern, reason = _pattern(pattern_text)
        if pattern is None:
            result.skip(number, line, reason)
            continue
        if exception:
            exceptions.append((number, line, pattern))
        elif "badfilter" in modifiers:
            badfilters.append((number, line, pattern))
        else:
            result.add(pattern, number)
    _cancel(result, badfilters, "被 $badfilter 规则禁用")
    _cancel(result, exceptions, "被 @@ 例外规则抵消")
    return result


def _is_hosts_line(line: str) -> bool:
    first = line.split(maxsplit=1)[0] if line.split() else ""
    try:
        parse_network(first)
    except AddressError:
        return False
    return "/" not in first and len(line.split()) >= 2


def _split_modifiers(body: str) -> tuple[str, set[str], str]:
    if body.startswith("/") and body.rstrip().endswith("/"):
        return body, set(), "AdGuard 正则方言与 Mihomo 正则引擎不保证一致"
    pattern, sep, tail = body.partition("$")
    modifiers: set[str] = set()
    if sep:
        for raw in tail.split(","):
            name = raw.split("=", 1)[0].strip().lower()
            if name not in DOCUMENTED_MODIFIERS:
                return pattern, modifiers, f"含官方文档未列出的修饰符 ${name}，按规定整条忽略"
            if name in CONDITIONAL_MODIFIERS:
                return pattern, modifiers, f"${name} 使规则只在特定条件下生效，无法等价转换"
            modifiers.add(name)
    return pattern.strip(), modifiers, ""


def _pattern(text: str) -> tuple[DomainPattern | None, str]:
    """把匹配部分转换为原生模式；只接受能精确表达的写法。"""
    body = text.removesuffix("|")
    if body.startswith("||") and body.endswith("^"):
        host, native_prefix = body[2:-1], "+."
        if host.startswith("*."):
            host, native_prefix = host[2:], "."
    elif body.startswith("|") and body.endswith("^"):
        host, native_prefix = body[1:-1], ""
    elif body and all(ch.isalnum() or ch in ".-_" for ch in body):
        host, native_prefix = body, ""
    else:
        return None, "只支持 ||域名^、|域名^ 与纯域名写法；该写法无法精确表达为域名集合"
    if not host or any(ch in host for ch in "*|^/:?"):
        return None, "局部通配或路径无法用原生域名模式等价表达"
    try:
        parse_network(host)
    except AddressError:
        pass
    else:
        return None, "IP 模式在 DNS 过滤中的含义不同于目标地址规则"
    try:
        return DomainPattern.parse_native(native_prefix + host.removesuffix(".")), ""
    except DomainError as exc:
        return None, str(exc)


def _cancel(
    result: ParseResult, cancels: list[tuple[int, str, DomainPattern]], reason: str
) -> None:
    for number, line, pattern in cancels:
        before = len(result.entries)
        result.entries = [e for e in result.entries if e.member != pattern]
        if len(result.entries) == before:
            result.skip(number, line, "无法在正向域名集合中表达该例外（没有完全相同的条目可抵消）")
        else:
            result.skip(number, line, reason)
