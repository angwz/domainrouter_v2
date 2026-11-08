"""宽泛规则：判定、上游过滤、手写保留与清单（docs/rules/broad-rules.md）。"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domainrouter_v2.breadth import Breadth, BreadthPolicy, Category, PublicSuffixes
from domainrouter_v2.build import BROAD_REPORT, build
from domainrouter_v2.config import load_config
from domainrouter_v2.diagnostics import Code
from domainrouter_v2.emit import read_payload
from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import parse_network
from domainrouter_v2.model.profile import Profile
from domainrouter_v2.parse.document import parse_profile
from domainrouter_v2.parse.rule_text import NoResolvePolicy, convert_condition
from domainrouter_v2.publish import stage_release
from domainrouter_v2.report import make_report
from domainrouter_v2.sources.fetch import fetch_all
from domainrouter_v2.sources.snapshot import StateStore

POLICY = BreadthPolicy.load()
EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal"
NOW = datetime(2026, 11, 8, tzinfo=UTC)
E, B, N = Breadth.EXCESSIVE, Breadth.BROAD, Breadth.NARROW


def rule(text: str) -> Breadth:
    return POLICY.classify(convert_condition(text, NoResolvePolicy.KEEP).member).level


def domain(text: str) -> Breadth:
    return POLICY.classify(DomainPattern.parse_native(text)).level


def network(text: str) -> Breadth:
    return POLICY.classify(parse_network(text).network).level


@pytest.mark.parametrize(
    ("text", "level"),
    [
        ("DOMAIN-KEYWORD,ads", E),  # 关键词表 [A]
        ("DOMAIN-KEYWORD,Analytics.", E),  # 大小写与首尾点不影响
        ("DOMAIN-KEYWORD,guanggao", E),  # 关键词表 [B]
        ("DOMAIN-KEYWORD,qq", E),  # ≤ 2 个字符
        ("DOMAIN-KEYWORD,jav", B),  # 3～4 个字符只提醒
        ("DOMAIN-KEYWORD,google", B),  # 品牌名只提醒
        ("DOMAIN-KEYWORD,uploads", B),  # 只比较整词，不做子串
        ("DOMAIN-REGEX,.*", E),
        ("DOMAIN-REGEX,^ad\\.", B),
        ("DOMAIN-REGEX,(", B),  # Python 无法编译：只提醒
        ("DOMAIN-WILDCARD,*", E),
        ("DOMAIN-WILDCARD,*.com", E),
        ("DOMAIN-WILDCARD,*.cn", B),
        ("DOMAIN-WILDCARD,ftp.??.debian.org", N),
        ("DOMAIN-WILDCARD,download*.mediafire.com", N),
        ("IP-CIDR,0.0.0.0/0,no-resolve", E),
        ("IP-CIDR6,::/0,no-resolve", E),
        ("SRC-IP-CIDR,0.0.0.0/0", E),
        ("SRC-IP-CIDR,192.168.0.0/16", N),
        ("IP-SUFFIX,8.8.8.8/0", E),
        ("IP-ASN,13335,no-resolve", B),
        ("GEOIP,CN,no-resolve", B),
        ("GEOSITE,cn", B),
        ("NETWORK,UDP", E),
        ("DST-PORT,443", E),
        ("DST-PORT,8000-9000", B),
        ("DST-PORT,1-65535", E),
        ("IN-PORT,7890", E),
        ("PROCESS-NAME,Telegram.exe", B),
        ("PROCESS-NAME-WILDCARD,*", E),
        ("PROCESS-NAME-REGEX,.*", E),
        ("AND,((NETWORK,UDP),(DST-PORT,443))", E),  # 全部 QUIC
        ("AND,((NETWORK,UDP),(DOMAIN,a.com))", N),  # 最窄的子条件决定范围
        ("OR,((DOMAIN,a.com),(NETWORK,TCP))", E),  # 最宽的子条件决定范围
        ("NOT,((DOMAIN,a.com))", E),
        ("NOT,((GEOSITE,cn))", B),
        ("DOMAIN-SUFFIX,a.com", N),
    ],
)
def test_condition_breadth(text: str, level: Breadth) -> None:
    assert rule(text) is level


@pytest.mark.parametrize(
    ("text", "level"),
    [
        ("example.com", N),
        ("+.example.com", N),
        ("+.go.com", N),  # go.com 不是公共后缀
        ("+.com", E),  # 通用顶级域
        ("*.org", E),
        ("+.cn", B),  # ccTLD：可能有意为之
        ("+.apple", B),  # 品牌 TLD 也只提醒
        ("+.ac.uk", B),  # 多级公共后缀
        (".gov.tw", B),
        ("*", B),  # 只匹配单标签主机名
        ("*.*", E),
        ("google.*", N),  # 左侧有固定标签
        ("com", N),  # 精确主机名
    ],
)
def test_domain_breadth(text: str, level: Breadth) -> None:
    assert domain(text) is level


@pytest.mark.parametrize(
    ("text", "level"),
    [
        ("0.0.0.0/0", E),
        ("128.0.0.0/1", E),
        ("::/0", E),
        ("2000::/3", E),  # 全部 IPv6 全球单播
        ("17.0.0.0/8", B),
        ("2400::/12", B),
        ("10.0.0.0/8", N),  # 本地地址不按大网段处理
        ("224.0.0.0/3", N),
        ("fc00::/7", N),
        ("1.0.0.0/9", N),
        ("240e::/18", N),
    ],
)
def test_network_breadth(text: str, level: Breadth) -> None:
    assert network(text) is level


def test_public_suffix_wildcard_and_exception() -> None:
    psl = PublicSuffixes.parse("ck\n*.ck\n!www.ck\nuk\nac.uk\n")
    assert psl.is_public_suffix("foo.ck")
    assert not psl.is_public_suffix("www.ck")
    assert psl.is_public_suffix("ac.uk")
    assert not psl.is_public_suffix("example.ac.uk")
    assert psl.is_public_suffix("anything")  # PSL 默认规则 "*"


def test_bundled_data_is_clean() -> None:
    assert POLICY.suffixes.is_public_suffix("com.cn")
    assert POLICY.suffixes.is_public_suffix("xn--fiqs8s")  # .中国 以 punycode 存放
    assert all(w == w.lower() and len(w) > 2 for w in POLICY.keywords)
    assert "google" not in POLICY.keywords  # 品牌名不收录


def test_verdict_has_category_and_reason() -> None:
    verdict = POLICY.classify(convert_condition("DOMAIN-KEYWORD,ads", NoResolvePolicy.KEEP).member)
    assert verdict.category is Category.KEYWORD
    assert "ads" in verdict.reason


# ---- 构建：上游过滤、手写保留、清单与发布 ----

UPSTREAM = b"\n".join(
    [
        b"DOMAIN-SUFFIX,video.example.com",
        b"DOMAIN-KEYWORD,ads,REJECT",
        b"DOMAIN-KEYWORD,examplestream",
        b"IP-CIDR,0.0.0.0/0,no-resolve",
        b"IP-CIDR,198.51.100.0/24,no-resolve",
        b"AND,((NETWORK,UDP),(DST-PORT,443)),REJECT",
    ]
)
SOURCE = "https://example.org/upstream.list"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    rules = root / "my.wei"
    text = rules.read_text(encoding="utf-8")
    extra = f"@source {SOURCE} format=surge\nDOMAIN-KEYWORD,cdn\n\n"
    text = text.replace("[Work]\n", extra + "[Work]\n")
    rules.write_bytes(text.encode("utf-8"))
    config = load_config(root / "config" / "domainrouter_v2.toml")

    def transport(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        return 200, {}, UPSTREAM

    refs = [ref for c in _profile(root).collections.values() for ref in c.sources]
    outcomes = fetch_all(refs, StateStore.open(config.state), config.fetch, transport)
    assert all(o.ok for o in outcomes), [o.message for o in outcomes]
    return root


def _profile(root: Path) -> Profile:
    return parse_profile((root / "my.wei").read_text(encoding="utf-8"), "my.wei").profile


def test_upstream_excessive_rules_are_filtered(project: Path) -> None:
    result = build(load_config(project / "config" / "domainrouter_v2.toml"))
    assert result.ok, [d.render() for d in result.diagnostics]
    filtered = {f.text for f in result.filtered}
    assert filtered == {
        "DOMAIN-KEYWORD,ads",
        "0.0.0.0/0",
        "AND,((NETWORK,UDP),(DST-PORT,443))",
    }
    dist = project / "dist"
    classic = read_payload((dist / "clash-classic" / "Streaming-classic.yaml").read_bytes())
    assert "DOMAIN-KEYWORD,ads" not in classic
    assert "DOMAIN-KEYWORD,examplestream" in classic
    assert "DOMAIN-KEYWORD,cdn" in classic  # 手写：通用词也原样保留
    ipcidr = read_payload((dist / "clash-ipcidr" / "Streaming-ipcidr.yaml").read_bytes())
    assert "0.0.0.0/0" not in ipcidr
    assert "198.51.100.0/24" in ipcidr
    codes = [d.code for d in result.diagnostics]
    assert Code.BROAD_FILTERED in codes
    assert Code.BROAD_RULE in codes  # 手写 DOMAIN-KEYWORD,cdn 的提醒


def test_broad_listing(project: Path) -> None:
    result = build(load_config(project / "config" / "domainrouter_v2.toml"))
    listing = result.files[BROAD_REPORT].decode("utf-8")
    assert "## 已过滤（3）" in listing
    assert "通用词「ads」在宽泛关键词表中" in listing
    assert SOURCE in listing
    assert "## 已发布：DOMAIN-KEYWORD" in listing
    assert "手写 · 通用词「cdn」" in listing
    assert "`examplestream`" in listing  # DOMAIN-KEYWORD 节只显示关键词


def test_yaml_header_and_sections(project: Path) -> None:
    result = build(load_config(project / "config" / "domainrouter_v2.toml"))
    text = result.files["clash-classic/Streaming-classic.yaml"].decode("utf-8")
    lines = text.splitlines()
    assert lines[0] == "# DomainRouter v2 · Streaming"
    assert "# 策略组：🎬 Media" in lines
    assert f"#   - {SOURCE}" in lines
    assert "  # DOMAIN-KEYWORD（3）" in lines
    # Mihomo 逐行解析：注释与空行之外的每一行都必须是 payload 头或条目
    for line in lines:
        stripped = line.strip()
        assert not stripped or stripped.startswith(("#", "payload:", "- '")), line
    assert "UTC" not in text and "2026" not in text  # 不含时间，保证确定性


def test_new_broad_rules_reported_and_published(project: Path, tmp_path: Path) -> None:
    config = load_config(project / "config" / "domainrouter_v2.toml")
    release = tmp_path / "release"
    result = build(config)
    report = make_report(config, result, None, NOW)
    assert {n["rule"] for n in report.broad_new} >= {"DOMAIN-KEYWORD,examplestream"}
    assert len(report.broad_filtered) == 3
    assert stage_release(release, result.files, report)
    assert (release / BROAD_REPORT).read_bytes() == result.files[BROAD_REPORT]
    latest = (release / "reports" / "latest.md").read_text(encoding="utf-8")
    assert "## 宽泛规则" in latest
    again = make_report(config, build(config), release, NOW)
    assert not again.broad_new
    assert not again.changed
