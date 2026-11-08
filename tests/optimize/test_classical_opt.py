"""classical 优化（merge-cases §7、§1 成本排序）。"""

from __future__ import annotations

from domainrouter_v2.model.rule import render_member
from domainrouter_v2.optimize.classical import optimize_classical
from domainrouter_v2.parse.rule_text import convert_condition


def run(*texts: str) -> list[str]:
    conditions = [convert_condition(t).member for t in texts]
    result, _ = optimize_classical(conditions)  # type: ignore[arg-type]
    return [render_member(c) for c in result]


def test_dedupe_and_keyword_case() -> None:
    assert run("DOMAIN-KEYWORD,ads", "DOMAIN-KEYWORD,ADS") == ["DOMAIN-KEYWORD,ads"]


def test_keyword_containment() -> None:
    assert run("DOMAIN-KEYWORD,google", "DOMAIN-KEYWORD,googleapis", "DOMAIN-KEYWORD,gstatic") == [
        "DOMAIN-KEYWORD,google",
        "DOMAIN-KEYWORD,gstatic",
    ]


def test_process_names_are_case_sensitive() -> None:
    assert run("PROCESS-NAME,A.exe", "PROCESS-NAME,a.exe") == [
        "PROCESS-NAME,A.exe",
        "PROCESS-NAME,a.exe",
    ]


def test_port_merge() -> None:
    assert run("DST-PORT,80", "DST-PORT,81", "DST-PORT,82", "DST-PORT,443", "SRC-PORT,80") == [
        "DST-PORT,80-82/443",
        "SRC-PORT,80",
    ]


def test_logic_not_commuted() -> None:
    a = "AND,((DOMAIN,a.com),(NETWORK,UDP))"
    b = "AND,((NETWORK,UDP),(DOMAIN,a.com))"
    assert run(a, a, b) == [a, b]


def test_cost_order() -> None:
    assert run(
        "PROCESS-NAME,x.exe",
        "DOMAIN-REGEX,^a$",
        "GEOIP,CN,no-resolve",
        "GEOSITE,cn",
        "DOMAIN-WILDCARD,*.a.com",
        "DOMAIN-KEYWORD,ads",
        "SRC-IP-CIDR,10.0.0.0/8",
        "NETWORK,UDP",
        "AND,((DOMAIN,a.com),(NETWORK,UDP))",
    ) == [
        "NETWORK,UDP",
        "SRC-IP-CIDR,10.0.0.0/8",
        "DOMAIN-KEYWORD,ads",
        "DOMAIN-WILDCARD,*.a.com",
        "GEOSITE,cn",
        "DOMAIN-REGEX,^a$",
        "GEOIP,CN,no-resolve",
        "AND,((DOMAIN,a.com),(NETWORK,UDP))",
        "PROCESS-NAME,x.exe",
    ]
