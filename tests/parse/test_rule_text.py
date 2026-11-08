"""显式规则行转换（merge-cases §3.4 规则列表）。"""

from __future__ import annotations

import pytest

from domainrouter_v2.model.rule import render_member
from domainrouter_v2.parse.rule_text import (
    NoResolvePolicy,
    ProblemKind,
    RuleProblem,
    convert_rule,
    looks_like_rule,
    normalize_ports,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("DOMAIN-SUFFIX,a.com,DIRECT", "+.a.com"),
        ("DOMAIN-KEYWORD,ads,REJECT", "DOMAIN-KEYWORD,ads"),
        ("DOMAIN,a.com,REJECT-TINYGIF", "a.com"),
        ("DOMAIN,a.com,Proxy,extended-matching", "a.com"),
        ("IP-CIDR,1.1.1.0/24,PROXY,no-resolve", "1.1.1.0/24"),
        ("IP-CIDR6,2001:db8::/32", "2001:db8::/32"),
        ("IP-CIDR,2001:db8::/32", "2001:db8::/32"),
        ("IP-CIDR,1.1.1.0/24,src", "SRC-IP-CIDR,1.1.1.0/24"),
        ("IP-ASN,13335", "IP-ASN,13335,no-resolve"),
        ("IP-ASN,AS13335", "IP-ASN,13335,no-resolve"),
        ("GEOIP,US,Proxy,no-resolve", "GEOIP,US,no-resolve"),
        ("GEOIP,CN,src", "SRC-GEOIP,CN"),
        ("DEST-PORT,443", "DST-PORT,443"),
        ("SRC-IP,192.168.1.2", "SRC-IP-CIDR,192.168.1.2/32"),
        ("PROTOCOL,UDP", "NETWORK,UDP"),
        ("DOMAIN-SUFFIX,.a.com", "+.a.com"),
        ("DOMAIN-KEYWORD,.tmall.com", "DOMAIN-KEYWORD,.tmall.com"),
        ("DOMAIN-KEYWORD,ADS", "DOMAIN-KEYWORD,ads"),
        ('DOMAIN-REGEX,"^a,b\\.com$",Proxy', "DOMAIN-REGEX,^a,b\\.com$"),
        ("DOMAIN-REGEX,^a{1,3}\\.com$,no-resolve", "DOMAIN-REGEX,^a{1,3}\\.com$"),
        (
            "AND,((DOMAIN,a.com),(NETWORK,UDP)),REJECT",
            "AND,((DOMAIN,a.com),(NETWORK,UDP))",
        ),
        (
            "AND,((IP-CIDR,1.0.0.0/8),(DST-PORT,443))",
            "AND,((IP-CIDR,1.0.0.0/8,no-resolve),(DST-PORT,443))",
        ),
        ("NOT,((DOMAIN-SUFFIX,a.com))", "NOT,((DOMAIN-SUFFIX,a.com))"),
        ("domain-suffix,A.com", "+.a.com"),
        ("DOMAIN,a.com.", "a.com"),
        ("DOMAIN,例子.com", "xn--fsqu00a.com"),
        ("DST-PORT,80/443", "DST-PORT,80/443"),
        ("PROCESS-NAME,Telegram.exe,Proxy", "PROCESS-NAME,Telegram.exe"),
    ],
)
def test_convert(text: str, expected: str) -> None:
    assert render_member(convert_rule(text).member) == expected


@pytest.mark.parametrize(
    "text",
    [
        "USER-AGENT,*Spotify*",
        "URL-REGEX,^https?://a\\.com/x",
        "PROTOCOL,QUIC",
        "SUBNET,SSID:home",
        "DOMAIN-SET,https://a/b.txt",
        "RULE-SET,https://a/b.list",
        "FINAL,DIRECT",
        "MATCH,DIRECT",
        "UNKNOWN-TYPE,x",
        "AND,((USER-AGENT,x),(NETWORK,TCP))",
    ],
)
def test_skipped(text: str) -> None:
    with pytest.raises(RuleProblem) as caught:
        convert_rule(text)
    assert caught.value.kind is ProblemKind.SKIP


@pytest.mark.parametrize(
    "text",
    [
        "DOMAIN-SUFFIX,*.a.com",
        "DOMAIN,+.a.com",
        "IP-CIDR,1.2.3.0/33",
        "NETWORK,ICMP",
        "AND,(DOMAIN,a.com",
        "NOT,((DOMAIN,a.com),(NETWORK,UDP))",
        "DST-PORT,70000",
        "DOMAIN-KEYWORD,",
    ],
)
def test_invalid(text: str) -> None:
    with pytest.raises(RuleProblem) as caught:
        convert_rule(text)
    assert caught.value.kind is ProblemKind.INVALID


def test_keep_policy_respects_user_params() -> None:
    keep = NoResolvePolicy.KEEP
    assert render_member(convert_rule("GEOIP,CN", keep).member) == "GEOIP,CN"
    assert render_member(convert_rule("GEOIP,JP,no-resolve", keep).member) == "GEOIP,JP,no-resolve"


def test_stripped_fields_are_recorded() -> None:
    result = convert_rule("DOMAIN-KEYWORD,ads,REJECT,extended-matching")
    assert result.stripped == ["REJECT", "extended-matching"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("80", "80"),
        ("1000-2000", "1000-2000"),
        ("1000:2000", "1000-2000"),
        (">=1024", "1024-65535"),
        (">1024", "1025-65535"),
        ("<1024", "0-1023"),
        ("<=1023", "0-1023"),
        ("80-80", "80"),
    ],
)
def test_ports(text: str, expected: str) -> None:
    assert normalize_ports(text) == expected


def test_looks_like_rule() -> None:
    assert looks_like_rule("DOMAIN,a.com")
    assert looks_like_rule("user-agent,x")
    assert not looks_like_rule("a.com")
    assert not looks_like_rule("hello,world")
