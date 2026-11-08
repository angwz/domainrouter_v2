"""产物序列化：provider YAML、rulesets.toml、groups.toml 与确定性清单。

所有文本输出为 UTF-8 无 BOM、LF、末尾一个换行；不写入时间等运行信息，
同一输入两次构建逐字节相同（规范 B01）。
provider 文件为 ``payload:`` 与单引号字符串条目：Mihomo 按行解析 YAML provider，
每行一个单引号标量最稳妥；条目内的单引号按 YAML 规则写成两个。
文件头与 classical 的分节标题是整行 ``#`` 注释，Mihomo 逐行解析时直接跳过
（rules/provider/provider.go 的 rulesParse）。注释只含由输入决定的信息，不含时间。
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tomli_w

import domainrouter_v2
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.profile import LocalMember, Profile
from domainrouter_v2.model.rule import Logic, Member, render_member
from domainrouter_v2.planner import CLASSICAL, IPCIDR, PARTITIONS, Artifact, Partition, Plan


def _item(member: Member) -> str:
    return "  - '" + render_member(member).replace("'", "''") + "'"


def _comments(header: Iterable[str]) -> list[str]:
    return [f"# {line}" if line else "#" for line in header]


def provider_yaml(members: Iterable[Member], header: Iterable[str] = ()) -> bytes:
    lines = [*_comments(header), "payload:"]
    lines.extend(_item(m) for m in members)
    return ("\n".join(lines) + "\n").encode("utf-8")


def read_payload(data: bytes) -> list[str]:
    """provider_yaml / classical_yaml 的逆操作：只取条目行，跳过注释与空行。"""
    items: list[str] = []
    for line in data.decode("utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- '") and stripped.endswith("'"):
            items.append(stripped[3:-1].replace("''", "'"))
    return items


def classical_yaml(members: list[Member], header: Iterable[str]) -> bytes:
    """classical 按类型分节：成员已按成本次序排好、同类型相邻，每节前加一行注释标题。"""
    lines = [*_comments(header), "payload:"]
    counts = Counter(_type_of(m) for m in members)
    previous = ""
    for member in members:
        kind = _type_of(member)
        if kind != previous:
            if previous:
                lines.append("")
            lines.append(f"  # {kind}（{counts[kind]}）")
            previous = kind
        lines.append(_item(member))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _type_of(member: Member) -> str:
    if isinstance(member, Logic):
        return member.op
    return render_member(member).split(",", 1)[0]


def artifact_header(
    artifact: Artifact, partition: Partition, profile: Profile, report_url: str
) -> list[str]:
    """文件头：内容摘要、策略组与合集来源。只用输入决定的信息，保证两次构建逐字节相同。"""
    members = artifact.members(partition)
    count = f"{partition.behavior} · {len(members)} 条"
    if partition is IPCIDR:
        v4 = sum(1 for m in members if isinstance(m, Network) and m.version == 4)
        count += f"（IPv4 {v4}，IPv6 {len(members) - v4}）"
    lines = [
        f"DomainRouter v2 · {' + '.join(artifact.collections)}",
        f"类型：{count}",
        f"策略组：{'、'.join(artifact.targets)}",
        "合集来源：",
    ]
    handwritten = 0
    seen: set[str] = set()
    for name in artifact.collections:
        for item in profile.collections[name].items:
            if isinstance(item, LocalMember):
                handwritten += 1
            elif item.url not in seen:
                seen.add(item.url)
                lines.append(f"  - {item.url}")
    if handwritten:
        lines.append(f"  - my.wei 手写 {handwritten} 条")
    lines += [
        "",
        f"更新说明：{report_url}",
        "由 domainrouter_v2 生成；请修改 my.wei，不要直接编辑本文件。",
    ]
    return lines


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
    """包内源码与数据（关键词表、PSL）的内容摘要：工作区改动也会反映；
    不依赖 git，也不含绝对路径和 mtime。"""
    root = Path(domainrouter_v2.__file__).parent
    digest = hashlib.sha256()
    paths = [*root.rglob("*.py"), *(root / "data").glob("*.txt")]
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b"\x00" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def render_outputs(
    plan: Plan,
    profile: Profile,
    groups_bytes: bytes,
    reports: dict[str, bytes],
    inputs: dict[str, Any],
    settings: dict[str, Any],
    report_url: str,
) -> dict[str, bytes]:
    """返回 {发布相对路径: 字节}。manifest 描述其余全部文件。"""
    files: dict[str, bytes] = dict(reports)
    artifacts: list[dict[str, Any]] = []
    for artifact in plan.artifacts.values():
        for partition in PARTITIONS:
            members = artifact.members(partition)
            if not members:
                continue
            path = artifact.path(partition)
            header = artifact_header(artifact, partition, profile, report_url)
            if partition is CLASSICAL:
                data = classical_yaml(members, header)
            else:
                data = provider_yaml(members, header)
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
        "reports": {path: sha256(data) for path, data in sorted(reports.items())},
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return files
