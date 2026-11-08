"""输出规划：路由块合并、命名与碰撞、空合集（merge-cases §9，规范 R01–R04、M09）。"""

from __future__ import annotations

import textwrap

from domainrouter_v2.diagnostics import Code, Level
from domainrouter_v2.model.rule import Member
from domainrouter_v2.parse.document import parse_profile
from domainrouter_v2.planner import build_plan, hashed_stem, preferred_stem, route_blocks


def plan_for(text: str, allow_empty: frozenset[str] = frozenset()):  # type: ignore[no-untyped-def]
    parsed = parse_profile(textwrap.dedent(text).lstrip("\n"), "my.wei")
    assert not [d for d in parsed.diagnostics if d.level is Level.ERROR]
    members: dict[str, list[Member]] = {
        name: [m.member for m in c.locals] for name, c in parsed.profile.collections.items()
    }
    plan = build_plan(
        parsed.profile,
        members,
        resource_url=lambda path: f"https://h/{path}",
        interval=21600,
        allow_empty=allow_empty,
    )
    return parsed.profile, plan


def test_adjacent_same_target_merged() -> None:
    profile, plan = plan_for(
        """
        [A]
        a.com
        [B]
        b.com
        [C]
        c.com
        [Rules]
        A: G
        B: G
        C: H
        A: G
        MATCH: G
        """
    )
    assert route_blocks(profile) == [(0, ("A", "B")), (2, ("C",)), (3, ("A",))]
    assert [e.ruleset for e in plan.rulesets] == [
        "https://h/clash-domain/A__B.yaml",
        "https://h/clash-domain/C.yaml",
        "https://h/clash-domain/A.yaml",
        "[]MATCH",
    ]
    merged = plan.artifacts[("A", "B")]
    assert [p.to_native() for p in merged.domains] == ["+.a.com", "+.b.com"]


def test_inline_rule_breaks_adjacency() -> None:
    profile, _ = plan_for(
        """
        [A]
        a.com
        [B]
        b.com
        [Rules]
        A: G
        GEOIP,CN: G
        B: G
        MATCH: G
        """
    )
    assert route_blocks(profile) == [(0, ("A",)), (2, ("B",))]


def test_partition_order_and_empty_partitions() -> None:
    _, plan = plan_for(
        """
        [A]
        a.com
        DOMAIN-KEYWORD,x
        [Rules]
        A: G
        GEOIP,JP: G,no-resolve
        MATCH: G
        """
    )
    assert [(e.type, e.ruleset) for e in plan.rulesets] == [
        ("clash-domain", "https://h/clash-domain/A.yaml"),
        ("clash-classic", "https://h/clash-classic/A-classic.yaml"),
        ("", "[]GEOIP,JP,no-resolve"),
        ("", "[]MATCH"),
    ]


def test_empty_referenced_collection() -> None:
    text = """
        [A]
        [B]
        b.com
        [Rules]
        A: G
        B: G
        MATCH: G
        """
    _, plan = plan_for(text.replace("B: G", "GEOIP,CN: G\n        B: G"))
    assert Code.EMPTY_COLLECTION in [d.code for d in plan.diagnostics]
    _, allowed = plan_for(text.replace("B: G", "GEOIP,CN: G\n        B: G"), frozenset({"A"}))
    assert Code.EMPTY_COLLECTION not in [d.code for d in allowed.diagnostics]


def test_unreferenced_collection_warning() -> None:
    _, plan = plan_for("[A]\na.com\n[Unused]\nb.com\n[Rules]\nA: G\nMATCH: G\n")
    assert [d.code for d in plan.diagnostics] == [Code.UNREFERENCED_COLLECTION]
    assert ("Unused",) not in plan.artifacts


def test_unsafe_names_use_hash() -> None:
    assert preferred_stem(("Example",)) == "Example"
    assert preferred_stem(("中国",)).startswith("c-")
    assert preferred_stem(("CON",)).startswith("c-")
    assert preferred_stem(("a b",)).startswith("c-")
    assert hashed_stem(("x",)) == hashed_stem(("x",))


def test_cross_behavior_collision_is_resolved() -> None:
    # 合集 A-ipcidr 的 domain 文件名与合集 A 的 ipcidr 文件名相同
    _, plan = plan_for(
        """
        [A]
        a.com
        192.0.2.0/24
        [A-ipcidr]
        b.com
        [Rules]
        A: G
        A-ipcidr: H
        MATCH: G
        """
    )
    names = [
        f"{art.stem}{p.suffix}".casefold()
        for art in plan.artifacts.values()
        for p in art.partitions()
    ]
    assert len(names) == len(set(names))
    assert plan.artifacts[("A",)].stem.startswith("c-")


def test_case_fold_collision() -> None:
    _, plan = plan_for("[ab]\na.com\n[AB]\nb.com\n[Rules]\nab: G\nAB: H\nMATCH: G\n")
    stems = {art.stem for art in plan.artifacts.values()}
    assert all(stem.startswith("c-") for stem in stems)
