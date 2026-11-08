"""DomainPattern：解析、规范化、包含判定与合并（merge-cases §2、§4、§5）。"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domainrouter_v2.model.domain import DomainError, DomainPattern
from domainrouter_v2.verify.reference import native_domain_match

P = DomainPattern.parse_native


@pytest.mark.parametrize(
    ("text", "canonical"),
    [
        ("a.hk", "a.hk"),
        ("+.a.hk", "+.a.hk"),
        (".a.hk", ".a.hk"),
        ("*.a.hk", "*.a.hk"),
        ("+.*.a.hk", ".a.hk"),  # 等价语言，唯一规范表示
        ("xbox.*.example.com", "xbox.*.example.com"),
        ("+.xbox.*.example.com", "+.xbox.*.example.com"),
        ("*", "*"),
        ("+.*", "+.*"),
        (".*", ".*"),
        ("*.*", "*.*"),
        ("A.Com", "a.com"),
        ("例子.hk", "xn--fsqu00a.hk"),
        ("_dmarc.a.com", "_dmarc.a.com"),
    ],
)
def test_parse_and_render(text: str, canonical: str) -> None:
    assert P(text).to_native() == canonical


@pytest.mark.parametrize(
    "text",
    ["", "a..com", "a.com.", "foo*.a.com", "a.+.com", "++.a.com", "+.", ".", "-a.com", "a b.com"],
)
def test_parse_rejects(text: str) -> None:
    with pytest.raises(DomainError):
        P(text)


def test_canonical_key_identity() -> None:
    assert P("+.*.a.hk") == P(".a.hk")
    assert P("a.hk").with_subdomain_closure() == P("+.a.hk")
    # 规范 §8.1：未加引号 *.a.hk 的「恰好 1」变为「至少 1」，不含自身
    assert P("*.a.hk").with_subdomain_closure() == P(".a.hk")
    assert P("xbox.*.example.com").with_subdomain_closure() == P("+.xbox.*.example.com")


# merge-cases §5：(覆盖者, 被覆盖者, 是否包含)
COVER_CASES = [
    ("+.a.com", "www.a.com", True),
    ("+.a.com", "+.b.a.com", True),
    ("+.a.com", "a.com", True),
    (".a.com", "x.a.com", True),
    (".a.com", "a.com", False),
    ("a.com", "x.a.com", False),
    ("+.a.com", "not-a.com", False),
    ("*.a.com", "x.a.com", True),
    ("*.a.com", "x.y.a.com", False),
    ("*.a.com", "a.com", False),
    (".a.com", "*.a.com", True),
    ("a.*.com", "a.b.com", True),
    ("a.*.com", "b.a.com", False),
    ("+.a.com", ".a.com", True),
    (".a.com", "+.a.com", False),
]


@pytest.mark.parametrize(("big", "small", "expected"), COVER_CASES)
def test_cover_cases(big: str, small: str, expected: bool) -> None:
    assert P(big).covers(P(small)) is expected


@pytest.mark.parametrize(
    ("a", "b", "merged"),
    [
        ("a.com", ".a.com", "+.a.com"),
        ("xbox.*.a.com", ".xbox.*.a.com", "+.xbox.*.a.com"),
        ("a.com", "*.a.com", None),  # 有限多值区间 [2,3] 无法单模式表达
        ("a.com", "b.com", None),
        ("+.a.com", ".a.com", "+.a.com"),
    ],
)
def test_union(a: str, b: str, merged: str | None) -> None:
    result = P(a).union(P(b))
    assert (result.to_native() if result else None) == merged


# ---- 穷举交叉校验：包含公式 vs 直接标签匹配（规范 §13.1） ----

ALPHABET = ["a", "b", "c"]
HOSTS = [".".join(labels) for n in range(1, 5) for labels in itertools.product(ALPHABET, repeat=n)]


def _patterns() -> list[str]:
    bodies = [
        ".".join(labels)
        for n in range(1, 4)
        for labels in itertools.product([*ALPHABET[:2], "*"], repeat=n)
    ]
    return [prefix + body for body in bodies for prefix in ("", "+.", ".")]


PATTERNS = _patterns()


def _language(pattern: str) -> frozenset[str]:
    return frozenset(h for h in HOSTS if native_domain_match(pattern, h))


def test_covers_matches_exhaustive_language_inclusion() -> None:
    """有限论域上，covers 的结论必须与「语言集合包含」一致。

    论域取长度 ≤ 4 的标签串，而模式至多 3 个固定标签外加 1 层额外前缀，
    且字母表含模式中未出现的标签 'c'，因此任何不包含都能在论域内找到反例。
    """
    languages = {p: _language(p) for p in PATTERNS}
    parsed = {p: P(p) for p in PATTERNS}
    for big, small in itertools.product(PATTERNS, repeat=2):
        expected = languages[small] <= languages[big]
        assert parsed[big].covers(parsed[small]) is expected, (big, small)


def test_render_roundtrip_preserves_language() -> None:
    for text in PATTERNS:
        assert _language(P(text).to_native()) == _language(text), text


# ---- 属性测试 ----

labels = st.sampled_from(["a", "b", "c", "*"])


@st.composite
def native_patterns(draw: st.DrawFn) -> str:
    body = ".".join(draw(st.lists(labels, min_size=1, max_size=3)))
    return draw(st.sampled_from(["", "+.", "."])) + body


@settings(max_examples=1000)
@given(native_patterns(), native_patterns())
def test_union_is_exact(a: str, b: str) -> None:
    merged = P(a).union(P(b))
    if merged is not None:
        assert _language(merged.to_native()) == _language(a) | _language(b)


@settings(max_examples=1000)
@given(native_patterns())
def test_parse_is_idempotent(text: str) -> None:
    once = P(text)
    assert P(once.to_native()) == once
