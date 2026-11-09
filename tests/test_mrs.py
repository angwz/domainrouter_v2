"""MRS 的路径约定与发布处理；编译本身用假的编译器代替（真实编译见 test_verify 的 kernel 用例）。"""

from __future__ import annotations

import shutil
import tomllib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domainrouter_v2.build import build
from domainrouter_v2.config import load_config
from domainrouter_v2.diagnostics import Code
from domainrouter_v2.emit import rulesets_toml
from domainrouter_v2.mrs import mrs_path
from domainrouter_v2.publish import stage_release
from domainrouter_v2.report import make_report

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal"
NOW = datetime(2026, 11, 9, tzinfo=UTC)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("clash-domain/China.yaml", "clash-domain/China.mrs"),
        ("clash-ipcidr/China-ipcidr.yaml", "clash-ipcidr/China-ipcidr.mrs"),
        ("clash-classic/China-classic.yaml", None),  # classical 没有 MRS
        ("rulesets.toml", None),
    ],
)
def test_mrs_path(path: str, expected: str | None) -> None:
    assert mrs_path(path) == expected


def test_missing_mihomo_is_a_build_error(tmp_path: Path) -> None:
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    config = replace(load_config(root / "config" / "domainrouter_v2.toml"), mrs=True)
    result = build(config, write=False)
    assert not result.ok
    assert any(
        d.code is Code.MRS_COMPILE and "tools prepare" in d.message for d in result.diagnostics
    )


def _with_fake_mrs(files: dict[str, bytes]) -> dict[str, bytes]:
    """模拟 build 产物中带有 MRS：内容由对应 YAML 决定，保证确定。"""
    out = dict(files)
    for path, data in files.items():
        target = mrs_path(path)
        if target is not None:
            out[target] = b"MRS\x00" + data[-16:]
    return out


def test_publish_writes_and_cleans_mrs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    config = load_config(root / "config" / "domainrouter_v2.toml")
    result = build(config, write=False)
    release = tmp_path / "release"
    assert stage_release(release, result.files, make_report(config, result, None, NOW))

    # 开启 MRS：规则条目不变，但新增 MRS 文件也要发布
    result.files = _with_fake_mrs(result.files)
    report = make_report(config, result, release, NOW)
    assert report.files_changed and not any(c.changed for c in report.changes)
    assert stage_release(release, result.files, report)
    mrs = release / "clash-domain" / "Streaming.mrs"
    assert mrs.read_bytes() == result.files["clash-domain/Streaming.mrs"]
    assert b"UPDATED" not in mrs.read_bytes()  # 二进制文件不写时间

    # 内容不变：不重新发布
    assert not make_report(config, result, release, NOW).changed

    # 关闭 MRS：发布时删除旧的 .mrs
    plain = build(config, write=False)
    report = make_report(config, plain, release, NOW)
    assert report.changed
    assert stage_release(release, plain.files, report)
    assert not mrs.exists()


def _example(tmp_path: Path):  # type: ignore[no-untyped-def]
    root = tmp_path / "project"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("dist", ".cache"))
    return load_config(root / "config" / "domainrouter_v2.toml")


def test_rulesets_mrs_mirrors_yaml_version(tmp_path: Path) -> None:
    result = build(_example(tmp_path), write=False)
    assert result.plan is not None
    yaml_entries = tomllib.loads(rulesets_toml(result.plan).decode())["rulesets"]
    mrs_entries = tomllib.loads(rulesets_toml(result.plan, binary=True).decode())["rulesets"]
    assert len(mrs_entries) == len(yaml_entries)
    for plain, binary in zip(yaml_entries, mrs_entries, strict=True):
        assert binary["group"] == plain["group"]
        assert binary.get("type") == plain.get("type")
        if plain.get("type") in {"clash-domain", "clash-ipcidr"}:
            assert binary["ruleset"] == plain["ruleset"].removesuffix(".yaml") + ".mrs"
        else:  # classical 与内联规则保持不变
            assert binary["ruleset"] == plain["ruleset"]


def test_rulesets_mrs_published_and_removed(tmp_path: Path) -> None:
    config = _example(tmp_path)
    result = build(config, write=False)
    assert result.plan is not None
    files = _with_fake_mrs(result.files)
    files["rulesets-mrs.toml"] = rulesets_toml(result.plan, binary=True)
    result.files = files
    release = tmp_path / "release"
    assert stage_release(release, files, make_report(config, result, None, NOW))
    assert (release / "rulesets-mrs.toml").is_file()

    plain = build(config, write=False)  # 关闭 MRS 后再发布
    report = make_report(config, plain, release, NOW)
    assert report.toml_changed
    assert stage_release(release, plain.files, report)
    assert not (release / "rulesets-mrs.toml").exists()
