"""my.wei 无损编辑：大纲、各编辑操作、格式保真与随机操作下的不变量。"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domainrouter_v2 import edit
from domainrouter_v2.diagnostics import Level
from domainrouter_v2.edit import EditError
from domainrouter_v2.parse.document import parse_profile

ROOT = Path(__file__).parents[1]
REAL = (ROOT / "my.wei").read_text(encoding="utf-8")

SAMPLE = """\
# 前言注释
[Streaming]
example.com
'api.example.net'

# DMIT
192.0.2.0/25
192.0.2.128/25
https://example.org/list.txt

[Work]
payload:
  - '+.corp.example'
  - 'vpn.example'
DST-PORT,8443

[Rules]
# 流媒体在前
Streaming: 🎬 Media
Work: 🧭 Proxy
GEOIP,CN: DIRECT
MATCH: 🐟 Final
"""


def lines_of(text: str) -> list[str]:
    return text.splitlines()


def errors(text: str) -> list[str]:
    parsed = parse_profile(text, "my.wei")
    return [d.message for d in parsed.diagnostics if d.level is Level.ERROR]


# ---- 大纲 ----


def test_outline_structure() -> None:
    tree = edit.outline(SAMPLE)
    assert [s.name for s in tree.sections] == ["", "Streaming", "Work", "Rules"]
    streaming = tree.section("Streaming")
    assert [u.text for u in streaming.units] == [
        "example.com",
        "'api.example.net'",
        "192.0.2.0/25",
        "192.0.2.128/25",
        "https://example.org/list.txt",
    ]
    first_ip = streaming.units[2]
    assert (first_ip.first, first_ip.line) == (6, 7)  # 「# DMIT」属于它
    assert first_ip.items[0].label == "IPv4 网段"
    assert streaming.units[0].items[0].text == "+.example.com"
    assert streaming.units[4].items[0].kind == "source"
    block = tree.section("Work").units[0]
    assert (block.kind, block.line, block.last) == ("block", 12, 14)
    assert [i.text for i in block.items] == ["+.corp.example", "vpn.example"]
    rules = tree.section("Rules").units
    assert rules[0].first == 18 and rules[0].route == edit.Route(
        "collection", "Streaming", "🎬 Media"
    )
    assert rules[2].route == edit.Route("inline", "GEOIP,CN", "DIRECT")
    assert rules[3].route is not None and rules[3].route.kind == "match"


def test_outline_reports_problems_by_line() -> None:
    tree = edit.outline(SAMPLE.replace("example.com\n", "foo*.example.com\n", 1))
    unit = tree.section("Streaming").units[0]
    assert unit.problems and "DOMAIN-WILDCARD" in unit.problems[0]


def test_real_profile_outline_covers_every_content_line() -> None:
    tree = edit.outline(REAL)
    covered = {n for s in tree.sections for u in s.units for n in range(u.line, u.last + 1)}
    headers = {s.header for s in tree.sections}
    for number, raw in enumerate(lines_of(REAL), 1):
        stripped = raw.strip()
        if stripped and not stripped.startswith(("#", ";", "//")) and number not in headers:
            assert number in covered, (number, raw)
    assert not tree.problems
    assert all(not u.problems for s in tree.sections for u in s.units)


# ---- 各操作 ----


def test_add_line_appends_after_last_unit() -> None:
    result = edit.add_line(SAMPLE, "Streaming", "  video.example  ")
    assert lines_of(result)[9] == "video.example"  # 第 9 行 list.txt 之后、空行之前
    assert lines_of(result)[:9] == lines_of(SAMPLE)[:9]
    assert lines_of(result)[10:] == lines_of(SAMPLE)[9:]


def test_add_line_after_a_unit() -> None:
    result = edit.add_line(SAMPLE, "Streaming", "a.example", after=3)
    assert lines_of(result)[3] == "a.example"


def test_add_route_goes_before_match() -> None:
    result = edit.add_line(SAMPLE, "Rules", "GEOIP,JP: 🎬 Media,no-resolve")
    assert lines_of(result)[-2:] == ["GEOIP,JP: 🎬 Media,no-resolve", "MATCH: 🐟 Final"]
    assert not errors(result)


def test_add_line_to_empty_section() -> None:
    text = edit.add_section(SAMPLE, "Empty")
    result = edit.add_line(text, "Empty", "x.example")
    tree = edit.outline(result)
    assert [u.text for u in tree.section("Empty").units] == ["x.example"]


def test_replace_keeps_indent() -> None:
    # 注意：紧跟在 payload: 块后的缩进行属于该块（与解析器一致），这里用普通合集中的行
    text = SAMPLE.replace("'api.example.net'", "  'api.example.net'")
    result = edit.replace_line(text, 4, "'www.example.net'")
    assert lines_of(result)[3] == "  'www.example.net'"


def test_indented_line_after_block_belongs_to_block() -> None:
    text = SAMPLE.replace("DST-PORT,8443", "    DST-PORT,8443")
    block = edit.outline(text).section("Work").units[0]
    assert (block.kind, block.last) == ("block", 15)


def test_delete_keeps_group_comment() -> None:
    result = edit.delete_unit(SAMPLE, 7)
    assert "# DMIT" in result and "192.0.2.0/25\n" not in result
    assert lines_of(result)[6] == "192.0.2.128/25"


def test_delete_block() -> None:
    result = edit.delete_unit(SAMPLE, 12)
    assert "payload:" not in result and "corp.example" not in result
    assert "DST-PORT,8443" in result


def test_add_section_before_rules() -> None:
    result = edit.add_section(SAMPLE, "Games")
    assert "DST-PORT,8443\n\n[Games]\n\n[Rules]" in result
    assert edit.outline(result).section("Games").units == []


def test_rename_updates_routes_only() -> None:
    result = edit.rename_section(SAMPLE, "Work", "Office")
    assert "[Office]" in result and "Office: 🧭 Proxy" in result
    assert "🧭 Proxy" in result and "Work" not in result
    assert not errors(result)


def test_delete_section_requires_no_routes() -> None:
    with pytest.raises(EditError, match="仍被"):
        edit.delete_section(SAMPLE, "Work")
    tree = edit.outline(SAMPLE)
    route = next(u for u in tree.section("Rules").units if u.text.startswith("Work:"))
    result = edit.delete_section(edit.delete_unit(SAMPLE, route.line), "Work")
    assert "[Work]" not in result and "DST-PORT" not in result
    assert not errors(result)


def test_reorder_moves_attached_comments() -> None:
    tree = edit.outline(SAMPLE)
    units = tree.section("Rules").units
    order = [units[1].line, units[0].line, units[2].line, units[3].line]
    result = edit.reorder_routes(SAMPLE, order)
    assert lines_of(result)[-5:] == [
        "Work: 🧭 Proxy",
        "# 流媒体在前",
        "Streaming: 🎬 Media",
        "GEOIP,CN: DIRECT",
        "MATCH: 🐟 Final",
    ]


def test_reorder_rejects_incomplete_order() -> None:
    with pytest.raises(EditError):
        edit.reorder_routes(SAMPLE, [19, 20])


@pytest.mark.parametrize(
    ("op", "message"),
    [
        ({"op": "add_line", "section": "Nope", "line_text": "a.b"}, "没有名为"),
        ({"op": "add_line", "section": "Work", "line_text": "[Bad]"}, "节标题"),
        ({"op": "add_line", "section": "Work", "line_text": "a\nb"}, "一行"),
        ({"op": "replace_line", "line": 12, "line_text": "x"}, "粘贴块"),
        ({"op": "replace_line", "line": 1, "line_text": "x"}, "不是一个可编辑的条目"),
        ({"op": "add_section", "name": "Rules"}, "保留名"),
        ({"op": "add_section", "name": "Work"}, "已存在"),
        ({"op": "rename_section", "name": "Rules", "new_name": "X"}, "不能重命名"),
        ({"op": "frobnicate"}, "未知操作"),
        ({"op": "delete_unit", "lines": 3}, "参数不正确"),
    ],
)
def test_errors(op: dict[str, object], message: str) -> None:
    with pytest.raises(EditError, match=message):
        edit.apply(SAMPLE, op)


# ---- 格式保真 ----


@pytest.mark.parametrize(
    "variant",
    [
        SAMPLE,
        SAMPLE.replace("\n", "\r\n"),  # CRLF
        SAMPLE.rstrip("\n"),  # 末尾无换行
        "﻿" + SAMPLE,  # BOM
        SAMPLE.replace("example.com\n", "example.com   \n", 1),  # 行尾空白
    ],
)
def test_format_is_preserved(variant: str) -> None:
    newline = "\r\n" if "\r\n" in variant else "\n"
    result = edit.add_line(variant, "Work", "z.example")
    assert result.startswith("﻿") == variant.startswith("﻿")
    assert result.endswith(newline) == variant.endswith(newline)
    assert ("\r\n" in result) == ("\r\n" in variant)
    assert result.replace(f"z.example{newline}", "", 1) == variant


def test_exotic_line_breaks_are_refused() -> None:
    with pytest.raises(EditError, match="换行"):
        edit.outline(SAMPLE + " ")


# ---- 单行预览 ----


@pytest.mark.parametrize(
    ("line", "text", "label"),
    [
        ("a.hk", "+.a.hk", "自身及全部子域"),
        ("'a.hk'", "a.hk", "仅自身"),
        ("*.a.hk", ".a.hk", "全部子域，不含自身"),
        ("'*.a.hk'", "*.a.hk", "通配，固定层级"),
        ("192.0.2.1", "192.0.2.1/32", "IPv4 网段"),
        ("DOMAIN-KEYWORD,x", "DOMAIN-KEYWORD,x", "DOMAIN-KEYWORD 规则"),
        ("https://e.org/a.list", "https://e.org/a.list", "上游来源"),
    ],
)
def test_describe_line(line: str, text: str, label: str) -> None:
    items, problems = edit.describe_line(line)
    assert not problems
    assert (items[0].text, items[0].label) == (text, label)


def test_describe_line_reports_problem() -> None:
    items, problems = edit.describe_line("foo*.example.com")
    assert not items and problems


def test_describe_route() -> None:
    items, problems = edit.describe_line("AI: 🗨️ ChatGPT", section="Rules")
    assert not problems and items[0].label == "→ 🗨️ ChatGPT"


# ---- 随机操作下的不变量（真实 my.wei） ----

_TREE = edit.outline(REAL)
_LINE_UNITS = [u for s in _TREE.sections if s.header and not s.is_rules for u in s.units]
_ROUTES = [u.line for u in _TREE.section("Rules").units]
_SECTIONS = [s.name for s in _TREE.sections if s.header and not s.is_rules]


@settings(max_examples=200, deadline=None)
@given(st.sampled_from(_LINE_UNITS))
def test_delete_touches_only_the_unit(unit: edit.Unit) -> None:
    before = lines_of(REAL)
    after = lines_of(edit.delete_unit(REAL, unit.line))
    assert after == before[: unit.line - 1] + before[unit.last :]


@settings(max_examples=200, deadline=None)
@given(st.sampled_from(_SECTIONS), st.from_regex(r"[a-z]{1,10}\.example", fullmatch=True))
def test_add_inserts_exactly_one_line(section: str, host: str) -> None:
    before = lines_of(REAL)
    after = lines_of(edit.add_line(REAL, section, host))
    assert len(after) == len(before) + 1
    position = next(i for i, line in enumerate(after) if i >= len(before) or line != before[i])
    assert after[position] == host
    assert after[:position] + after[position + 1 :] == before
    tree = edit.outline("\n".join(after) + "\n")
    added = [u for u in tree.section(section).units if u.text == host]
    assert added and added[0].items[0].text == f"+.{host}"


@settings(max_examples=100, deadline=None)
@given(st.permutations(_ROUTES))
def test_reorder_is_a_permutation_of_rules_only(order: list[int]) -> None:
    rules = _TREE.section("Rules")
    before = lines_of(REAL)
    after = lines_of(edit.reorder_routes(REAL, order))
    assert after[: rules.header] == before[: rules.header]  # [Rules] 之前逐字节不变
    assert sorted(after) == sorted(before)
    routes = [u.text for u in edit.outline("\n".join(after)).section("Rules").units]
    assert routes == [before[n - 1].strip() for n in order]


def test_noop_roundtrip_is_byte_identical() -> None:
    assert edit._Document.load(REAL).dump() == REAL
    for variant in (REAL.replace("\n", "\r\n"), REAL.rstrip("\n"), "﻿" + REAL):
        assert edit._Document.load(variant).dump() == variant
