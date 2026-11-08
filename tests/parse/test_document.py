"""my.wei 文档解析（规范 §4，merge-cases §2、§9 的内联部分）。"""

from __future__ import annotations

import textwrap

import pytest

from domainrouter_v2.diagnostics import Code, Level
from domainrouter_v2.model.profile import LocalMember, RouteKind, SourceRef
from domainrouter_v2.model.rule import render_member
from domainrouter_v2.parse.document import parse_profile, split_route


def parse(text: str):  # type: ignore[no-untyped-def]
    return parse_profile(textwrap.dedent(text).lstrip("\n"), "my.wei")


def local(text: str, name: str = "X") -> list[str]:
    parsed = parse(f"[{name}]\n{text}\n[Rules]\n{name}: G\nMATCH: G\n")
    errors = [d for d in parsed.diagnostics if d.level is Level.ERROR]
    assert not errors, [d.render() for d in errors]
    return [render_member(m.member) for m in parsed.profile.collections[name].locals]


def errors_of(text: str) -> list[Code]:
    parsed = parse(f"[X]\n{text}\n[Rules]\nX: G\nMATCH: G\n")
    return [d.code for d in parsed.diagnostics if d.level is Level.ERROR]


# ---- 规范 §4.2 语义表（D01–D06、D16、D19、D20） ----


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("a.hk", "+.a.hk"),
        ("'a.hk'", "a.hk"),
        ('"a.hk"', "+.a.hk"),
        ("DOMAIN,a.hk", "a.hk"),
        ("DOMAIN-SUFFIX,a.hk", "+.a.hk"),
        ("'*.a.hk'", "*.a.hk"),
        ("*.a.hk", ".a.hk"),
        ("'.a.hk'", ".a.hk"),
        (".a.hk", ".a.hk"),
        ("'+.a.hk'", "+.a.hk"),
        ("+.a.hk", "+.a.hk"),
        ("'xbox.*.example.com'", "xbox.*.example.com"),
        ("xbox.*.example.com", "+.xbox.*.example.com"),
        ("‘a.hk’", "a.hk"),
        ("“a.hk”", "+.a.hk"),
        ("A.HK.", "+.a.hk"),
        ("例子.hk", "+.xn--fsqu00a.hk"),
        ("- a.hk", "+.a.hk"),
        ("- 'a.hk'", "a.hk"),
        ("`a.hk`", "+.a.hk"),
        ("DOMAIN-SUFFIX,'a.hk'", "+.a.hk"),
        ("'*'", "*"),
        ("'+.*'", "+.*"),
        ("a.hk # 注释", "+.a.hk"),
        ("192.0.2.1", "192.0.2.1/32"),
        ("'192.0.2.0/24'", "192.0.2.0/24"),
        ("2001:db8::/32", "2001:db8::/32"),
        ("DST-PORT,9993", "DST-PORT,9993"),
        ("GEOIP,CN", "GEOIP,CN,no-resolve"),
        ("DOMAIN-KEYWORD,nodeseek", "DOMAIN-KEYWORD,nodeseek"),
    ],
)
def test_free_line_semantics(line: str, expected: str) -> None:
    assert local(line) == [expected]


@pytest.mark.parametrize(
    ("line", "code"),
    [
        ("'a.hk", Code.PARSE_AMBIGUOUS),
        ("*", Code.PARSE_AMBIGUOUS),
        ("+", Code.PARSE_AMBIGUOUS),
        (".", Code.PARSE_AMBIGUOUS),
        ("foo*.example.com", Code.PARSE_AMBIGUOUS),
        ("DOMAIN-SUFFIX,*.a.hk", Code.PARSE_AMBIGUOUS),
        ("DOMAIN,*.a.hk", Code.PARSE_AMBIGUOUS),
        ("a.+.hk", Code.PARSE_AMBIGUOUS),
        ("USER-AGENT,x", Code.TARGET_UNSUPPORTED),
        ("MATCH,DIRECT", Code.TARGET_UNSUPPORTED),
    ],
)
def test_free_line_errors(line: str, code: Code) -> None:
    assert errors_of(line) == [code]


# ---- 节、指令与块（P01、P06、P11） ----


def test_sections_and_brackets_in_rules() -> None:
    parsed = parse(
        r"""
        [A]
        DOMAIN-REGEX,^[a-z]+\.example\.com$
        [B]
        b.com
        [Rules]
        A: G1
        B: G2
        MATCH: G3
        """
    )
    assert list(parsed.profile.collections) == ["A", "B"]
    assert not [d for d in parsed.diagnostics if d.level is Level.ERROR]


def test_duplicate_collection_merges_with_warning() -> None:
    parsed = parse("[A]\na.com\n[A]\nb.com\n[Rules]\nA: G\nMATCH: G\n")
    assert len(parsed.profile.collections["A"].locals) == 2
    assert [d.code for d in parsed.diagnostics] == [Code.DUPLICATE_SECTION]


def test_duplicate_rules_section_is_error() -> None:
    parsed = parse("[A]\na.com\n[Rules]\nA: G\n[Rules]\nMATCH: G\n")
    assert Code.PARSE_SYNTAX in [d.code for d in parsed.diagnostics]


def test_directives() -> None:
    parsed = parse(
        """
        [A]
        https://example.org/rules.yaml
        @source https://example.org/domains.txt format=surge-domainset
        @source https://example.org/c.yaml format=clash-config exclude_types=MATCH,FINAL
        @site https://www.Example.com:8443/path?x=1
        @site http://192.0.2.7/x
        [Rules]
        A: G
        MATCH: G
        """
    )
    items = parsed.profile.collections["A"].items
    sources = [i for i in items if isinstance(i, SourceRef)]
    assert [(s.format, s.exclude_types) for s in sources] == [
        ("auto", ()),
        ("surge-domainset", ()),
        ("clash-config", ("MATCH", "FINAL")),
    ]
    locals_ = [render_member(i.member) for i in items if isinstance(i, LocalMember)]
    assert locals_ == ["+.www.example.com", "192.0.2.7/32"]


@pytest.mark.parametrize(
    "line",
    [
        "@source https://a/b format=quanx",
        "@source https://a/b colour=red",
        "@source https://a/b exclude_types=MATCH",
        "@source https://a/b format=clash-config exclude_types=DOMAIN",
        "@source notaurl",
        "@unknown x",
        "@end",
    ],
)
def test_directive_errors(line: str) -> None:
    assert errors_of(line)


def test_explicit_block() -> None:
    members = local(
        "@begin format=domain\npayload:\n  - '*.a.hk'\n  - '+.b.hk'\n@end\nc.hk",
    )
    # 显式块中的单引号只是 YAML 容器：'*.a.hk' 仍是恰好一级子域
    assert members == ["*.a.hk", "+.b.hk", "+.c.hk"]


def test_explicit_block_section_header_is_content() -> None:
    """块内的节标题属于该格式的内容，不会开启新节。"""
    body = "[X]\n@begin format=surge-domainset\n.a.hk\n[Y]\n@end\n"
    parsed = parse(body + "[Rules]\nX: G\nMATCH: G\n")
    assert list(parsed.profile.collections) == ["X"]
    assert [render_member(m.member) for m in parsed.profile.collections["X"].locals] == ["+.a.hk"]
    assert [d.code for d in parsed.diagnostics] == [Code.RULE_SKIPPED]


def test_explicit_block_wei_uses_handwritten_semantics() -> None:
    assert local("@begin format=wei\na.hk\n'b.hk'\n@end") == ["+.a.hk", "b.hk"]


def test_explicit_block_missing_end() -> None:
    assert Code.PARSE_SYNTAX in errors_of("@begin format=domain\na.hk")


def test_implicit_payload_block_ends_at_column_zero() -> None:
    members = local("payload:\n  - '*.a.hk'\n  # note\n\n  - b.hk\nc.hk")
    assert members == ["*.a.hk", "b.hk", "+.c.hk"]


def test_isolated_list_item_uses_handwritten_semantics() -> None:
    assert local("- '*.a.hk'") == ["*.a.hk"]
    assert local("- *.a.hk") == [".a.hk"]


def test_rules_block_strips_policy() -> None:
    assert local("rules:\n  - DOMAIN-SUFFIX,a.com,DIRECT\n  - GEOIP,CN,DIRECT") == [
        "+.a.com",
        "GEOIP,CN,no-resolve",
    ]


# ---- [Rules]（R03、P02、P03、P10、merge-cases §9） ----


def test_rules_section() -> None:
    parsed = parse(
        """
        [A]
        a.com
        [B]
        b.com
        [Rules]
        A: 🌠 节点选择
        GEOIP,CN: DIRECT
        GEOIP,JP: 🌺 日本专线,no-resolve
        IP-CIDR6,2001:db8::/32: DIRECT
        B:DIRECT
        A: G
        FINAL: 🐳 漏网の鱼
        """
    )
    routes = parsed.profile.routes
    assert [r.kind for r in routes] == [
        RouteKind.COLLECTION,
        RouteKind.INLINE,
        RouteKind.INLINE,
        RouteKind.INLINE,
        RouteKind.COLLECTION,
        RouteKind.COLLECTION,
        RouteKind.MATCH,
    ]
    assert [r.target for r in routes] == [
        "🌠 节点选择",
        "DIRECT",
        "🌺 日本专线",
        "DIRECT",
        "DIRECT",
        "G",
        "🐳 漏网の鱼",
    ]
    assert routes[1].inline_text == "GEOIP,CN"  # 手写不带 no-resolve，原样保留
    assert routes[2].inline_text == "GEOIP,JP,no-resolve"
    assert routes[3].inline_text == "IP-CIDR6,2001:db8::/32"
    assert not [d for d in parsed.diagnostics if d.level is Level.ERROR]


@pytest.mark.parametrize(
    ("rules", "code"),
    [
        ("Nope: G\nMATCH: G", Code.ROUTE_REFERENCE),
        ("X: G,no-resolve\nMATCH: G", Code.ROUTE_REFERENCE),
        ("X: G", Code.ROUTE_FALLBACK),
        ("MATCH: G\nX: G", Code.ROUTE_FALLBACK),
        ("MATCH: G\nMATCH: H", Code.ROUTE_FALLBACK),
        ("GEOIP,CN: G,bogus\nMATCH: G", Code.ROUTE_REFERENCE),
        ("DOMAIN-REGEX,^a{1,2}$: G\nMATCH: G", Code.BACKEND_LOSSY),
        ("AND,((DOMAIN,a.com),(NETWORK,UDP)): G\nMATCH: G", Code.BACKEND_LOSSY),
        ("USER-AGENT,x: G\nMATCH: G", Code.TARGET_UNSUPPORTED),
    ],
)
def test_rules_errors(rules: str, code: Code) -> None:
    parsed = parse(f"[X]\na.com\n[Rules]\n{rules}\n")
    assert code in [d.code for d in parsed.diagnostics if d.level is Level.ERROR]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A: G", ("A", "G")),
        ("IP-CIDR6,2001:db8::/32: DIRECT", ("IP-CIDR6,2001:db8::/32", "DIRECT")),
        ("DOMAIN-REGEX,^(?:a|b)\\.com$: G", ("DOMAIN-REGEX,^(?:a|b)\\.com$", "G")),
        ("DOMAIN-REGEX,[a: b]: G", ("DOMAIN-REGEX,[a: b]", "G")),
        ("A:G", None),
    ],
)
def test_split_route(text: str, expected: tuple[str, str] | None) -> None:
    assert split_route(text) == expected
