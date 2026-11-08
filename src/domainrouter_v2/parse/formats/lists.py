"""逐行域名列表类格式：Surge DOMAIN-SET、hosts、dnsmasq。

- Surge DOMAIN-SET（https://manual.nssurge.com/rules/domain.html）：
  ``.x`` 表示 x 自身及全部子域（与 Mihomo 的 ``.x`` 相反），其他行为精确域名；``#``、``//`` 为注释。
- hosts（hosts(5)）：``IP 主机名 [别名…]``，每个名字都是精确域名；``#`` 起到行尾为注释。
- dnsmasq（dnsmasq(8)）：``server=/d1/d2/…/值`` 等指令按完整标签匹配域名及子域；
  ``/*.d/`` 仅子域；``/#/`` 匹配全部域名，``//`` 仅无点主机名，均跳过。
"""

from __future__ import annotations

from domainrouter_v2.parse.formats.base import ParseResult, iter_lines
from domainrouter_v2.parse.formats.common import add_exact_or_suffix, add_native_domain

HOSTS_LOCAL_NAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "local",
        "broadcasthost",
        "ip6-localhost",
        "ip6-loopback",
        "ip6-localnet",
        "ip6-mcastprefix",
        "ip6-allnodes",
        "ip6-allrouters",
        "ip6-allhosts",
        "0.0.0.0",
    }
)
DNSMASQ_DIRECTIVES = ("server=", "local=", "address=", "ipset=", "nftset=")


def parse_surge_domainset(text: str) -> ParseResult:
    result = ParseResult("surge-domainset")
    for number, line in iter_lines(text):
        if not line or line.startswith(("#", "//")):
            continue
        if line.startswith(".") and not line.startswith(".."):
            add_exact_or_suffix(result, number, line[1:], suffix=True)
        else:
            add_exact_or_suffix(result, number, line, suffix=False)
    return result


def parse_hosts(text: str) -> ParseResult:
    result = ParseResult("hosts")
    for number, raw in iter_lines(text):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) < 2:
            result.skip(number, raw, "hosts 行至少需要地址和一个主机名", invalid=True)
            continue
        for name in fields[1:]:
            if name.lower() in HOSTS_LOCAL_NAMES:
                continue  # 本机名不是分流目标，按约定忽略且不计入跳过
            add_exact_or_suffix(result, number, name, suffix=False)
    return result


def parse_dnsmasq(text: str) -> ParseResult:
    result = ParseResult("dnsmasq")
    for number, line in iter_lines(text):
        if not line or line.startswith("#"):
            continue
        if not line.startswith(DNSMASQ_DIRECTIVES):
            continue  # 其他配置项与域名规则无关
        _, _, value = line.partition("=")
        if not value.startswith("/"):
            continue  # 不带域名的指令（如 server=1.1.1.1）
        parts = value.split("/")
        # "/a/b/1.1.1.1" → ["", "a", "b", "1.1.1.1"]：首尾之间是域名
        domains = parts[1:-1]
        if not domains:
            result.skip(number, line, "缺少域名部分", invalid=True)
            continue
        for domain in domains:
            if domain in {"", "#"}:
                reason = "'//' 只匹配无点主机名" if domain == "" else "'/#/' 匹配全部域名"
                result.skip(number, line, reason)
            elif domain.startswith("*."):
                add_native_domain(result, number, "." + domain[2:])
            else:
                add_exact_or_suffix(result, number, domain, suffix=True)
    return result
