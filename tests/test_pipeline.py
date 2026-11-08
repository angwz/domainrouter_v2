"""端到端：最小示例构建、确定性、失败不覆盖、发布与无变化跳过（规范 B01、B04、B09、A03）。"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domainrouter_v2.build import build
from domainrouter_v2.cli import main
from domainrouter_v2.config import load_config
from domainrouter_v2.emit import read_payload
from domainrouter_v2.publish import stage_release
from domainrouter_v2.report import make_report

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal"
NOW = datetime(2026, 11, 8, tzinfo=UTC)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    return root


def test_example_builds(project: Path) -> None:
    result = build(load_config(project / "config" / "domainrouter_v2.toml"))
    assert result.ok, [d.render() for d in result.diagnostics]
    dist = project / "dist"
    assert read_payload((dist / "clash-domain" / "Streaming.yaml").read_bytes()) == [
        "+.example.com",
        "api.example.net",
        ".cdn.example.org",
    ]
    assert read_payload((dist / "clash-ipcidr" / "Streaming-ipcidr.yaml").read_bytes()) == [
        "192.0.2.0/24"
    ]
    toml = (dist / "rulesets.toml").read_text(encoding="utf-8")
    assert 'ruleset = "[]GEOIP,CN"' in toml
    assert toml.rstrip().endswith('ruleset = "[]MATCH"')


def test_build_is_deterministic(project: Path) -> None:
    config = load_config(project / "config" / "domainrouter_v2.toml")
    first = build(config, write=False).files
    second = build(config, write=False).files
    assert first == second


def test_failed_build_keeps_previous_output(project: Path) -> None:
    config = load_config(project / "config" / "domainrouter_v2.toml")
    assert build(config).ok
    before = (project / "dist" / "rulesets.toml").read_bytes()
    rules = project / "my.wei"
    rules.write_text(rules.read_text(encoding="utf-8") + "\n[Broken]\n'unbalanced\n", "utf-8")
    assert not build(config).ok
    assert (project / "dist" / "rulesets.toml").read_bytes() == before


def test_input_is_never_modified(project: Path) -> None:
    rules = project / "my.wei"
    before = rules.read_bytes()
    build(load_config(project / "config" / "domainrouter_v2.toml"))
    assert rules.read_bytes() == before


def test_publish_and_unchanged_skip(project: Path, tmp_path: Path) -> None:
    config = load_config(project / "config" / "domainrouter_v2.toml")
    release = tmp_path / "release"
    result = build(config)
    report = make_report(config, result, None, NOW)
    assert stage_release(release, result.files, report)
    assert (release / "reports" / "latest.md").exists()
    assert (release / "manifest.json").read_bytes() != b""
    again = build(config)
    report2 = make_report(config, again, release, NOW)
    assert not report2.changed
    assert not stage_release(release, again.files, report2)


def test_publish_removes_stale_files(project: Path, tmp_path: Path) -> None:
    config = load_config(project / "config" / "domainrouter_v2.toml")
    release = tmp_path / "release"
    result = build(config)
    stage_release(release, result.files, make_report(config, result, None, NOW))
    rules = project / "my.wei"
    rules.write_text(rules.read_text(encoding="utf-8").replace("DST-PORT,8443\n", ""), "utf-8")
    changed = build(config)
    report = make_report(config, changed, release, NOW)
    assert report.changed
    stage_release(release, changed.files, report)
    assert not (release / "clash-classic" / "Work-classic.yaml").exists()


def test_cli_exit_codes(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = str(project / "config" / "domainrouter_v2.toml")
    assert main(["check", "--config", cfg]) == 0
    assert main(["build", "--config", cfg]) == 0
    assert main(["build", "--config", str(project / "missing.toml")]) == 2
    (project / "my.wei").write_text("[A]\n'x\n[Rules]\nA: DIRECT\nMATCH: DIRECT\n", "utf-8")
    assert main(["check", "--config", cfg]) == 2
    capsys.readouterr()
