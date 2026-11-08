"""验证层：subconverter 订阅模拟、语义对照、explain，以及（可选）真实 Mihomo 对照。"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from typing import ClassVar

import pytest

from domainrouter_v2.build import build
from domainrouter_v2.config import load_config
from domainrouter_v2.explain import explain
from domainrouter_v2.planner import RulesetEntry
from domainrouter_v2.tools import ToolError, find_executable, load_specs
from domainrouter_v2.verify.kernel import emulate_subscription, find_file_name, run_kernel
from domainrouter_v2.verify.semantic import verify_artifact

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal"


@pytest.fixture
def example(tmp_path: Path):  # type: ignore[no-untyped-def]
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    config = load_config(root / "config" / "domainrouter_v2.toml")
    result = build(config, write=False)
    assert result.ok
    return config, result


@pytest.mark.parametrize(
    ("url", "name"),
    [
        ("https://h/release/clash-domain/Example.yaml", "Example"),
        ("https://h/release/clash-ipcidr/Example-ipcidr.yaml", "Example-ipcidr"),
        ("https://h/a.b/clash-classic/X.Y-classic.yaml", "X.Y-classic"),
    ],
)
def test_find_file_name(url: str, name: str) -> None:
    assert find_file_name(url) == name


def test_emulate_subscription_matches_fork_rules() -> None:
    class FakePlan:
        rulesets: ClassVar[list[RulesetEntry]] = [
            RulesetEntry("G", "https://h/clash-domain/A.yaml", "clash-domain", 1),
            RulesetEntry("G", "https://h/clash-ipcidr/A-ipcidr.yaml", "clash-ipcidr", 1),
            RulesetEntry("H", "https://h/clash-domain/A.yaml", "clash-domain", 1),
            RulesetEntry("DIRECT", "[]GEOIP,CN"),
            RulesetEntry("JP", "[]GEOIP,JP,no-resolve"),
            RulesetEntry("F", "[]FINAL"),
        ]

    rules, providers = emulate_subscription(FakePlan())  # type: ignore[arg-type]
    assert rules == [
        "RULE-SET,A,G",
        "RULE-SET,A-ipcidr,G,no-resolve",
        "RULE-SET,A_2,H",  # 重复引用：fork 追加 _2
        "GEOIP,CN,DIRECT",
        "GEOIP,JP,JP,no-resolve",  # 三个逗号：fork 正则把组名移到参数前
        "MATCH,F",
    ]
    assert providers["A_2"] == ("domain", "clash-domain/A.yaml")


def test_semantic_verification_on_example(example) -> None:  # type: ignore[no-untyped-def]
    _, result = example
    for names, artifact in result.plan.artifacts.items():
        raw = [m for n in names for m in result.collection_members[n]]
        outcome = verify_artifact(artifact, raw)
        assert outcome.ok, outcome.mismatches


def test_explain_on_example(example) -> None:  # type: ignore[no-untyped-def]
    _, result = example
    text = explain(result, host="video.cdn.example.org").render()
    assert "结论：[0] Streaming → 🎬 Media（domain 集合）" in text
    text = explain(result, host="example.edu").render()
    assert "结论：[1] Work → 🧭 Proxy（domain 集合）" in text
    text = explain(result, ip="192.0.2.200").render()
    assert "Streaming" in text and "ipcidr 集合" in text
    text = explain(result, host="unknown.invalid").render()
    assert "MATCH" in text


def _tools_ready(state: Path) -> bool:
    try:
        specs = load_specs()
        for name, candidates in (("mihomo", ["mihomo*"]), ("go", ["go/bin/go*"])):
            find_executable(state, specs[name], candidates)
    except ToolError:
        return False
    return True


@pytest.mark.kernel
def test_kernel_on_example(example, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    config, result = example
    shared = Path(__file__).parents[1] / ".cache" / "domainrouter_v2"
    if not _tools_ready(shared):
        pytest.skip("未运行 domainrouter_v2 tools prepare")
    outcome = run_kernel(replace(config, state=shared), result)
    assert outcome.ok, outcome.mismatches + outcome.count_mismatches
    # 示例中唯一会请求 DNS 解析的是手写且不带 no-resolve 的 GEOIP,CN
    assert set(outcome.resolve_rules) <= {"GeoIP,cn"}
