"""配置校验与策略组校验。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from domainrouter_v2.config import ConfigError, parse_config
from domainrouter_v2.diagnostics import Code, Level
from domainrouter_v2.groups import validate_groups

BASE: dict[str, Any] = {
    "schema_version": 1,
    "project_root": "..",
    "output": {"base_url": "https://raw.githubusercontent.com/o/domainrouter_v2/release"},
}


def config(tmp_path: Path, **overrides: Any) -> Any:
    data = {**BASE, **overrides}
    return parse_config(data, tmp_path / "config" / "domainrouter_v2.toml")


def test_paths_resolve_from_config_location(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    assert cfg.project_root == tmp_path.resolve()
    assert cfg.rules == (tmp_path / "my.wei").resolve()
    assert cfg.output == (tmp_path / "dist").resolve()


def test_resource_url_is_encoded(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    assert cfg.resource_url("clash-domain/A B.yaml") == (
        "https://raw.githubusercontent.com/o/domainrouter_v2/release/clash-domain/A%20B.yaml"
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": 2},
        {"unknown": 1},
        {"output": {"base_url": "ftp://x/y"}},
        {"output": {"base_url": "https://u:p@x/y"}},
        {"output": {"base_url": "https://x/y?q=1"}},
        {"output": {"base_url": "https://raw.githubusercontent.com/YOUR_OWNER/domainrouter_v2"}},
        {"output": {"base_url": "https://x/y", "directory": "."}},
        {"output": {"base_url": "https://x/y", "directory": "src"}},
        {"output": {"base_url": "https://x/y", "interval_seconds": 0}},
        {"fetch": {"max_workers": 0}},
        {"fetch": {"shrink_threshold": 1.5}},
        {"fetch": {"bogus": 1}},
        {"policy": {"allow_empty_collections": "A"}},
    ],
)
def test_invalid_config(tmp_path: Path, overrides: dict[str, Any]) -> None:
    with pytest.raises(ConfigError):
        config(tmp_path, **overrides)


GROUPS_OK = """
[[custom_groups]]
name = "Proxy"
type = "select"
rule = ["[]HK", "[]DIRECT", "(.*)"]

[[custom_groups]]
name = "HK"
type = "fallback"
rule = ["(港|HK)"]
url = "https://www.gstatic.com/generate_204"
interval = 300
"""


def codes(text: str) -> list[Code]:
    return [
        d.code for d in validate_groups(text, "groups.toml").diagnostics if d.level is Level.ERROR
    ]


def test_groups_ok() -> None:
    result = validate_groups(GROUPS_OK, "groups.toml")
    assert result.names == ["Proxy", "HK"]
    assert not result.diagnostics


@pytest.mark.parametrize(
    ("text", "code"),
    [
        (GROUPS_OK.replace("[]HK", "[]Nope"), Code.GROUP_REFERENCE),
        (GROUPS_OK.replace('rule = ["(港|HK)"]', 'rule = ["[]Proxy"]'), Code.GROUP_CYCLE),
        (GROUPS_OK.replace("interval = 300", ""), Code.GROUP_INVALID),
        (GROUPS_OK.replace('type = "select"', 'type = "magic"'), Code.GROUP_INVALID),
        (GROUPS_OK.replace('name = "Proxy"', 'name = "A,B"'), Code.GROUP_INVALID),
        (
            GROUPS_OK + GROUPS_OK.split("[[custom_groups]]")[1].join(["[[custom_groups]]", ""]),
            Code.GROUP_INVALID,
        ),
        ("not toml [", Code.GROUP_INVALID),
    ],
)
def test_groups_errors(text: str, code: Code) -> None:
    assert code in codes(text)
