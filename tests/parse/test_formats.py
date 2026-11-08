"""来源格式适配器与自动识别（merge-cases §3）。"""

from __future__ import annotations

import json

import pytest

from domainrouter_v2.model.rule import render_member
from domainrouter_v2.parse.formats import SourceFormatError, detect_format, parse_source
from domainrouter_v2.parse.yaml_safe import (
    YamlStructureError,
    _fast_path,
    _full_parse,
    load_list_document,
)


def members(text: str, fmt: str) -> list[str]:
    return [render_member(e.member) for e in parse_source(text, fmt).entries]


def skipped(text: str, fmt: str) -> list[str]:
    return [s.text for s in parse_source(text, fmt).skipped]


# ---- §3.2 自动识别 ----


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("payload:\n  - '+.a.com'\n", "mihomo"),
        ("# c\nDOMAIN-SUFFIX,a.com\nIP-CIDR,1.0.0.0/8,no-resolve\n", "surge"),
        ("a.com\nb.com\n", "mihomo"),
        ("+.a.com\nb.com\n", "mihomo"),
        ("server=/a.com/1.1.1.1\ncache-size=100\n", "dnsmasq"),
        ("! title\n||a.com^\n", "adguard"),
        ("0.0.0.0 a.com\n127.0.0.1 localhost\n", "hosts"),
        (json.dumps({"version": 2, "rules": [{"domain": ["a.com"]}]}), "singbox"),
    ],
)
def test_detect(text: str, expected: str) -> None:
    assert detect_format(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        ".a.com\nb.com\n",  # 前导点含义在 Surge/Mihomo 中相反
        "<!DOCTYPE html><html></html>",
        "",
        "DOMAIN,a.com\nb.com\nc.com\nd.com\n",  # 规则与裸域名混杂
    ],
)
def test_detect_ambiguous(text: str) -> None:
    with pytest.raises(SourceFormatError):
        detect_format(text)


def test_binary_rejected() -> None:
    with pytest.raises(SourceFormatError):
        parse_source("MRS\x00\x01", "auto")


# ---- §3.3 Mihomo ----


def test_mihomo_domain_yaml() -> None:
    text = "payload:\n  - '+.a.com'\n  - '.b.com'\n  - c.com\n  - '*.d.com'\n  - e.com/path\n"
    assert members(text, "domain") == ["+.a.com", ".b.com", "c.com", "*.d.com"]
    assert skipped(text, "domain") == ["e.com/path"]


def test_mihomo_ipcidr_text() -> None:
    assert members("1.2.3.4\n1.2.3.5/24\n# c\n", "ipcidr") == ["1.2.3.4/32", "1.2.3.0/24"]


def test_mihomo_classical_routes_to_sets() -> None:
    text = "payload:\n  - DOMAIN-SUFFIX,a.com\n  - IP-CIDR,1.0.0.0/8\n  - GEOIP,CN\n  - MATCH\n"
    assert members(text, "classical") == ["+.a.com", "1.0.0.0/8", "GEOIP,CN,no-resolve"]
    assert skipped(text, "classical") == ["MATCH"]


def test_mihomo_auto_behavior_splits_mixed_payload() -> None:
    text = "payload:\n  - a.com\n  - 1.2.3.4\n"
    assert members(text, "mihomo") == ["a.com", "1.2.3.4/32"]


def test_mihomo_domain_repairs() -> None:
    result = parse_source("A.com.\n1.2.3.4\n", "domain")
    assert [render_member(e.member) for e in result.entries] == ["a.com", "1.2.3.4/32"]
    assert all(e.notes for e in result.entries)


@pytest.mark.parametrize(
    "text",
    [
        "payload:\n  - a\npayload:\n  - b\n",  # 重复键
        "payload: &x\n  - a\nother: *x\n",  # 锚点/别名
        "payload:\n  - yes\n",  # 布尔
        "payload:\n  - 1\n",  # 整数
        "payload:\n  - !!str a\n",  # tag
        "payload:\n  - a\n---\npayload:\n  - b\n",  # 多文档
    ],
)
def test_yaml_rejects_unsafe(text: str) -> None:
    with pytest.raises((YamlStructureError, SourceFormatError)):
        load_list_document(text)


@pytest.mark.parametrize(
    "text",
    [
        "payload:\n  - '+.a.com'\n  - b.com # c\n  - \"c.com\"\n  - 'it''s'\n",
        "---\npayload:\n  - DOMAIN,a.com\n  - IP-CIDR,1.0.0.0/8,no-resolve\n",
        "payload:\n  - '*.a.com'\n  - .b.com\n",
    ],
)
def test_yaml_fast_path_equals_full_parse(text: str) -> None:
    assert _fast_path(text) == _full_parse(text)


# ---- §3.4 规则列表 ----


def test_rulelist() -> None:
    text = "\n".join(
        [
            "# NAME: x",
            "DOMAIN-SUFFIX,a.com,DIRECT",
            "DOMAIN,b.com // trailing",
            "; comment",
            "USER-AGENT,*Spotify*",
            "a.com",
            "IP-CIDR,1.1.1.0/24,no-resolve",
        ]
    )
    assert members(text, "surge") == ["+.a.com", "b.com", "1.1.1.0/24"]
    assert skipped(text, "surge") == ["USER-AGENT,*Spotify*", "a.com"]


def test_rulelist_keeps_regex_hash() -> None:
    assert members("DOMAIN-REGEX,^a #b$\n", "surge") == ["DOMAIN-REGEX,^a #b$"]


# ---- §3.5 Surge DOMAIN-SET ----


def test_surge_domainset_leading_dot_includes_self() -> None:
    assert members("a.com\n.b.com\n# c\n", "surge-domainset") == ["a.com", "+.b.com"]


# ---- §3.6 sing-box ----


def sb(*rules: object) -> str:
    return json.dumps({"version": 3, "rules": list(rules)})


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ({"domain": ["a.com"]}, ["a.com"]),
        ({"domain_suffix": ["a.com"]}, ["+.a.com"]),
        ({"domain_suffix": ".a.com"}, [".a.com"]),
        ({"domain_keyword": ["ads"]}, ["DOMAIN-KEYWORD,ads"]),
        ({"domain_regex": ["^a\\.com$"]}, ["DOMAIN-REGEX,^a\\.com$"]),
        ({"ip_cidr": ["1.0.0.0/8"]}, ["1.0.0.0/8"]),
        ({"source_ip_cidr": ["10.0.0.0/8"]}, ["SRC-IP-CIDR,10.0.0.0/8"]),
        (
            {"domain_suffix": ["a.com"], "port": [443]},
            ["AND,((DOMAIN-SUFFIX,a.com),(DST-PORT,443))"],
        ),
        ({"port_range": ["1000:2000"]}, ["DST-PORT,1000-2000"]),
        ({"network": "udp"}, ["NETWORK,UDP"]),
        ({"process_name": ["a.exe"]}, ["PROCESS-NAME,a.exe"]),
        ({"invert": True, "domain": ["a.com"]}, ["NOT,((DOMAIN,a.com))"]),
        (
            {"type": "logical", "mode": "or", "rules": [{"domain": "a.com"}, {"domain": "b.com"}]},
            ["a.com", "b.com"],
        ),
    ],
)
def test_singbox(rule: dict[str, object], expected: list[str]) -> None:
    assert members(sb(rule), "singbox") == expected


def test_singbox_unsupported_field_skips_whole_rule() -> None:
    text = sb({"domain": ["a.com"], "wifi_ssid": ["home"]})
    assert members(text, "singbox") == []
    assert len(parse_source(text, "singbox").skipped) == 1


def test_singbox_bad_version() -> None:
    with pytest.raises(SourceFormatError):
        parse_source(json.dumps({"version": 9, "rules": []}), "singbox")


# ---- §3.7 AdGuard ----


def test_adguard() -> None:
    text = "\n".join(
        [
            "! comment",
            "||a.com^",
            "||b.com^$important",
            "|c.com^",
            "d.com",
            "||*.e.com^",
            "0.0.0.0 f.com",
            "||g.com^$client=1.2.3.4",
            "||h.com^$unknownmod",
            "/ads[0-9]+\\.com/",
            "||ad*.i.com^",
            "||1.2.3.4^",
            "example.org##.banner",
        ]
    )
    assert members(text, "adguard") == ["+.a.com", "+.b.com", "c.com", "d.com", ".e.com", "f.com"]
    assert len(skipped(text, "adguard")) == 6


def test_adguard_exception_and_badfilter() -> None:
    text = "||a.com^\n||b.com^\n@@||a.com^\n||b.com^$badfilter\n@@||x.b.com^\n"
    assert members(text, "adguard") == []
    reasons = [s.reason for s in parse_source(text, "adguard").skipped]
    assert len(reasons) == 3


# ---- §3.8 hosts ----


def test_hosts() -> None:
    text = "127.0.0.1 localhost\n::1 ip6-localhost\n0.0.0.0 a.com b.com # c\n0.0.0.0 0.0.0.0\n"
    assert members(text, "hosts") == ["a.com", "b.com"]


# ---- §3.9 dnsmasq ----


def test_dnsmasq() -> None:
    text = "\n".join(
        [
            "server=/a.com/114.114.114.114",
            "server=/b.com/c.com/1.1.1.1",
            "address=/d.com/0.0.0.0",
            "local=/e.com/",
            "ipset=/f.com/set1",
            "nftset=/g.com/4#inet#t#s",
            "server=/*.h.com/1.1.1.1",
            "server=/#/1.1.1.1",
            "server=//1.1.1.1",
            "server=1.1.1.1",
            "cache-size=100",
        ]
    )
    assert members(text, "dnsmasq") == [
        "+.a.com",
        "+.b.com",
        "+.c.com",
        "+.d.com",
        "+.e.com",
        "+.f.com",
        "+.g.com",
        ".h.com",
    ]
    assert len(skipped(text, "dnsmasq")) == 2
