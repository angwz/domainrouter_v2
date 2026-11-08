"""domain 集合优化（merge-cases §5，规范 D07–D10、D14、D17、D18、B02）。"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.optimize.domain import optimize_domains
from domainrouter_v2.verify.reference import native_domain_match

P = DomainPattern.parse_native


def run(*texts: str) -> list[str]:
    result, _ = optimize_domains([P(t) for t in texts])
    return sorted(p.to_native() for p in result)


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        (("+.a.com", "www.a.com"), ["+.a.com"]),
        (("+.a.com", "+.b.a.com"), ["+.a.com"]),
        (("+.a.com", "a.com"), ["+.a.com"]),
        ((".a.com", "a.com"), ["+.a.com"]),
        ((".a.com", "x.a.com"), [".a.com"]),
        (("a.com", "x.a.com"), ["a.com", "x.a.com"]),
        (("+.a.com", "not-a.com"), ["+.a.com", "not-a.com"]),
        (("x.a.com", "y.a.com", "z.a.com"), ["x.a.com", "y.a.com", "z.a.com"]),
        (("*.a.com", "x.a.com"), ["*.a.com"]),
        (("*.a.com", "x.y.a.com"), ["*.a.com", "x.y.a.com"]),
        (("*.a.com", "a.com"), ["*.a.com", "a.com"]),
        ((".a.com", "*.a.com"), [".a.com"]),
        (("a.*.com", "a.b.com"), ["a.*.com"]),
        (("a.*.com", "b.a.com"), ["a.*.com", "b.a.com"]),
        (("xbox.*.a.com", ".xbox.*.a.com"), ["+.xbox.*.a.com"]),
        (("+.a.com", "+.a.com", "+.a.com"), ["+.a.com"]),
        # 合并产生新的包含：a.com + .a.com → +.a.com，再吞掉 x.a.com
        (("a.com", ".a.com", "x.a.com", "+.b.a.com"), ["+.a.com"]),
        # 多层：后缀被更大的后缀覆盖，链条最终指向存活代表
        (("+.c.b.a.com", "+.b.a.com", "+.a.com"), ["+.a.com"]),
    ],
)
def test_cases(inputs: tuple[str, ...], expected: list[str]) -> None:
    assert run(*inputs) == expected


def test_events_point_to_survivors() -> None:
    result, events = optimize_domains([P(t) for t in ("x.a.com", "a.com", ".a.com", "+.c.a.com")])
    survivors = set(result)
    assert all(coverer in survivors for coverer in events.covered.values())
    assert events.merged == {P("+.a.com"): (P("a.com"), P(".a.com"))}


# ---- 属性测试：语言不变、无残留包含、幂等 ----

ALPHABET = ["a", "b", "c"]
HOSTS = [".".join(p) for n in range(1, 6) for p in itertools.product(ALPHABET, repeat=n)]


def language(patterns: list[DomainPattern]) -> frozenset[str]:
    natives = [p.to_native() for p in patterns]
    return frozenset(h for h in HOSTS if any(native_domain_match(n, h) for n in natives))


@st.composite
def pattern(draw: st.DrawFn) -> DomainPattern:
    labels = draw(st.lists(st.sampled_from([*ALPHABET[:2], "*"]), min_size=1, max_size=3))
    return P(draw(st.sampled_from(["", "+.", "."])) + ".".join(labels))


@settings(max_examples=1000)
@given(st.lists(pattern(), max_size=10))
def test_optimization_is_exact(patterns: list[DomainPattern]) -> None:
    result, _ = optimize_domains(patterns)
    assert language(result) == language(patterns)
    for a, b in itertools.permutations(result, 2):
        assert not a.covers(b), (a, b)
    again, _ = optimize_domains(result)
    assert again == result
