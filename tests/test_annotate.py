"""来源标注：字母编号、来源简称与同行注释格式。"""

from __future__ import annotations

from domainrouter_v2.annotate import _letter, _short, annotate
from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.provenance import HANDWRITTEN, ArtifactTrace, Trace

URL_B = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Adobe/Adobe.list"
URL_C = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/adobe.yaml"


def d(text: str) -> DomainPattern:
    return DomainPattern.parse_native(text)


def test_letters() -> None:
    assert [_letter(i) for i in (0, 25, 26, 27, 51, 52)] == ["A", "Z", "AA", "AB", "AZ", "BA"]


def test_short_names() -> None:
    assert _short(URL_B) == "blackmatrix7 · Adobe/Adobe.list"
    assert _short(URL_C) == "MetaCubeX · geosite/adobe.yaml"
    assert _short("https://ruleset.skk.moe/Clash/domainset/cdn.txt") == (
        "ruleset.skk.moe · domainset/cdn.txt"
    )
    assert _short(HANDWRITTEN) == HANDWRITTEN


def test_note_lists_sources_merges_and_covered() -> None:
    covered = tuple((d(f"h{i}.adobe.com"), frozenset({URL_C})) for i in range(5))
    trace = ArtifactTrace(
        traces={
            d("+.adobe.com"): Trace(frozenset({URL_B, URL_C}), (), covered),
            d("+.a.com"): Trace(
                frozenset(),
                ((d("a.com"), frozenset({HANDWRITTEN})), (d(".a.com"), frozenset({URL_B}))),
                (),
            ),
        },
        labels=[HANDWRITTEN, URL_B, URL_C],
    )
    result = annotate([d("+.a.com"), d("+.adobe.com")], trace)
    assert result.legend == [
        "SOURCE A: my.wei",
        "SOURCE B: blackmatrix7 · Adobe/Adobe.list",
        "SOURCE C: MetaCubeX · geosite/adobe.yaml",
    ]
    assert result.notes[d("+.a.com")] == "合并 .a.com B, a.com A"
    assert result.notes[d("+.adobe.com")] == ("B C  覆盖 h0.adobe.com C, h1.adobe.com C 等 5 条")


def test_only_used_sources_get_letters() -> None:
    trace = ArtifactTrace(
        traces={d("x.com"): Trace(frozenset({URL_C}), (), ())},
        labels=[HANDWRITTEN, URL_B, URL_C],
    )
    result = annotate([d("x.com")], trace)
    assert result.legend == ["SOURCE A: MetaCubeX · geosite/adobe.yaml"]
    assert result.notes[d("x.com")] == "A"
