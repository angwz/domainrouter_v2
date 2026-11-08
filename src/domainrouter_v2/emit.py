"""产物序列化：provider YAML、rulesets.toml、groups.toml 与确定性清单。

所有文本输出为 UTF-8 无 BOM、LF、末尾一个换行；不写入时间等运行信息，
同一输入两次构建逐字节相同（规范 B01）。
provider 文件只含 ``payload:`` 与单引号字符串条目：Mihomo 按行解析 YAML provider，
每行一个单引号标量最稳妥；条目内的单引号按 YAML 规则写成两个。
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tomli_w

import domainrouter_v2
from domainrouter_v2.model.rule import Member, render_member
from domainrouter_v2.planner import PARTITIONS, Plan


def provider_yaml(members: Iterable[Member]) -> bytes:
    lines = ["payload:"]
    lines.extend("  - '" + render_member(m).replace("'", "''") + "'" for m in members)
    return ("\n".join(lines) + "\n").encode("utf-8")


def rulesets_toml(plan: Plan) -> bytes:
    data = {"rulesets": [entry.as_toml() for entry in plan.rulesets]}
    return tomli_w.dumps(data).encode("utf-8")


def normalized_text(raw: bytes) -> bytes:
    text = raw.decode("utf-8").removeprefix("﻿").replace("\r\n", "\n").replace("\r", "\n")
    return (text.rstrip("\n") + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    """规范 JSON：键按码点排序、无多余空白、UTF-8（规范 §11.5）。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def engine_fingerprint() -> str:
    """包内源码内容摘要：工作区改动也会反映；不依赖 git，也不含绝对路径和 mtime。"""
    root = Path(domainrouter_v2.__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b"\x00" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def render_outputs(
    plan: Plan,
    groups_bytes: bytes,
    inputs: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, bytes]:
    """返回 {发布相对路径: 字节}。manifest 描述其余全部文件。"""
    files: dict[str, bytes] = {}
    artifacts: list[dict[str, Any]] = []
    for artifact in plan.artifacts.values():
        for partition in PARTITIONS:
            members = artifact.members(partition)
            if not members:
                continue
            path = artifact.path(partition)
            data = provider_yaml(members)
            files[path] = data
            artifacts.append(
                {
                    "path": path,
                    "behavior": partition.behavior,
                    "format": "yaml",
                    "collections": list(artifact.collections),
                    "entries": len(members),
                    "sha256": sha256(data),
                }
            )
    files["rulesets.toml"] = rulesets_toml(plan)
    files["groups.toml"] = normalized_text(groups_bytes)
    identity = {
        "generator": f"domainrouter_v2 {domainrouter_v2.__version__}",
        "engine": engine_fingerprint(),
        "inputs": inputs,
        "settings": settings,
    }
    manifest = {
        "schema_version": 1,
        **identity,
        "generation": sha256(canonical_json(identity)),
        "artifacts": sorted(artifacts, key=lambda a: a["path"]),
        "rulesets": {"entries": len(plan.rulesets), "sha256": sha256(files["rulesets.toml"])},
        "groups": {"sha256": sha256(files["groups.toml"])},
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return files
