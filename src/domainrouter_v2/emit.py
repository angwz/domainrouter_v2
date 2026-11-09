"""产物序列化：provider YAML、rulesets.toml、groups.toml 与确定性清单。

所有文本输出为 UTF-8 无 BOM、LF、末尾一个换行；不写入时间等运行信息，
同一输入两次构建逐字节相同（规范 B01）。
provider 文件为 ``payload:`` 与单引号字符串条目：Mihomo 按行解析 YAML provider，
每行一个单引号标量最稳妥；条目内的单引号按 YAML 规则写成两个。
文件头是整行 ``#`` 注释，classical 的类型之间是空行，Mihomo 逐行解析时都直接跳过
（rules/provider/provider.go 的 rulesParse）。每条规则的来源标注是同行注释：该行与
``payload:`` 一起交给 YAML 解析器，注释被解析器忽略（见 annotate.py）。
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import tomli_w

import domainrouter_v2
from domainrouter_v2.annotate import annotate
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.rule import Logic, Member, render_member
from domainrouter_v2.planner import CLASSICAL, DOMAIN, PARTITIONS, Artifact, Partition, Plan
from domainrouter_v2.provenance import ArtifactTrace

UPDATED_KEY = "UPDATED"
UPDATED_ZONE = timezone(timedelta(hours=8), "UTC+8")


# 同行注释的对齐列：取本文件 90% 条目都能放下的宽度，但不超过 NOTE_COLUMN_MAX；
# 更长的条目只隔两个空格，避免少数长域名把整列推得很远。
NOTE_COLUMN_MAX = 56
_NOTE_GAP = 2


def _item(member: Member) -> str:
    return "  - '" + render_member(member).replace("'", "''") + "'"


def _comments(header: Iterable[str]) -> list[str]:
    return [f"# {line}" for line in header]


def _width(text: str) -> int:
    """等宽字体中的显示宽度：全角与宽字符占两列（如进程名中的中文）。"""
    if text.isascii():
        return len(text)  # 绝大多数条目（域名已是 punycode）走这条快速路径
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _item_lines(members: list[Member], notes: dict[Member, str] | None) -> list[str]:
    items = [_item(m) for m in members]
    if not notes or not items:
        return items
    widths = sorted(_width(item) for item in items)
    column = min(widths[(len(widths) * 9) // 10], NOTE_COLUMN_MAX) + _NOTE_GAP
    lines: list[str] = []
    for member, item in zip(members, items, strict=True):
        note = notes.get(member)
        if note:
            pad = max(column - _width(item), _NOTE_GAP)
            lines.append(f"{item}{' ' * pad}# {note}")
        else:
            lines.append(item)
    return lines


def provider_yaml(
    members: list[Member], header: Iterable[str] = (), notes: dict[Member, str] | None = None
) -> bytes:
    lines = [*_comments(header), "payload:", *_item_lines(members, notes)]
    return ("\n".join(lines) + "\n").encode("utf-8")


def classical_yaml(
    members: list[Member], header: Iterable[str], notes: dict[Member, str] | None = None
) -> bytes:
    """classical：成员已按成本次序排好、同类型相邻，类型之间空一行。"""
    lines = [*_comments(header), "payload:"]
    previous = ""
    for member, line in zip(members, _item_lines(members, notes), strict=True):
        kind = _type_of(member)
        if previous and kind != previous:
            lines.append("")
        previous = kind
        lines.append(line)
    return ("\n".join(lines) + "\n").encode("utf-8")


def read_payload(data: bytes) -> list[str]:
    """provider_yaml / classical_yaml 的逆操作：只取条目，跳过注释、空行与同行注释。"""
    items: list[str] = []
    for line in data.decode("utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- '"):
            items.append(_single_quoted(stripped, 3))
    return items


def _single_quoted(text: str, start: int) -> str:
    """从 start 起读取 YAML 单引号标量的内容（``''`` 表示一个单引号）。"""
    out: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "'":
            if text.startswith("''", i):
                out.append("'")
                i += 2
                continue
            return "".join(out)
        out.append(ch)
        i += 1
    raise ValueError(f"单引号未闭合：{text!r}")


def _type_of(member: Member) -> str:
    if isinstance(member, Network):
        return "IP-CIDR" if member.version == 4 else "IP-CIDR6"
    if isinstance(member, Logic):
        return member.op
    return render_member(member).split(",", 1)[0]


def artifact_header(artifact: Artifact, partition: Partition, repository: str) -> list[str]:
    """文件头：``KEY: value`` 每行一项。只含由输入决定的信息，两次构建逐字节相同；
    更新时间由发布时的 stamp_updated 写入（build 产物不含时间）。"""
    members = artifact.members(partition)
    fields = [("NAME", " + ".join(artifact.collections)), ("GROUP", ", ".join(artifact.targets))]
    if repository:
        fields.append(("REPO", repository))
    fields += [("TYPE", partition.behavior), ("TOTAL", str(len(members)))]
    if partition is not DOMAIN:
        counts = Counter(_type_of(m) for m in members)  # 按文件中首次出现的顺序
        if len(counts) > 1:
            fields += [(kind, str(n)) for kind, n in counts.items()]
    return [f"{key}: {value}" for key, value in fields]


def stamp_updated(data: bytes, when: datetime) -> bytes:
    """在 ``# TYPE:`` 之前插入 ``# UPDATED: …``。只在发布时调用，build 产物保持确定。"""
    stamp = f"# {UPDATED_KEY}: {when.astimezone(UPDATED_ZONE):%Y-%m-%d %H:%M:%S} (UTC+8)\n"
    text = data.decode("utf-8")
    index = text.find("# TYPE: ")
    if index < 0:
        raise ValueError("provider 文件缺少 TYPE 行")
    return (text[:index] + stamp + text[index:]).encode("utf-8")


def strip_updated(data: bytes) -> bytes:
    """stamp_updated 的逆操作，用于判断已发布文件除时间外是否与新产物相同。"""
    prefix = f"# {UPDATED_KEY}: ".encode()
    return b"".join(line for line in data.splitlines(keepends=True) if not line.startswith(prefix))


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
    groups_bytes: bytes,
    documents: dict[str, bytes],
    inputs: dict[str, Any],
    settings: dict[str, Any],
    repository: str,
    traces: dict[tuple[str, ...], ArtifactTrace],
) -> dict[str, bytes]:
    """返回 {发布相对路径: 字节}。manifest 描述其余全部文件。"""
    files: dict[str, bytes] = dict(documents)
    artifacts: list[dict[str, Any]] = []
    for names, artifact in plan.artifacts.items():
        for partition in PARTITIONS:
            members = artifact.members(partition)
            if not members:
                continue
            path = artifact.path(partition)
            annotation = annotate(members, traces[names])
            header = artifact_header(artifact, partition, repository) + annotation.legend
            if partition is CLASSICAL:
                data = classical_yaml(members, header, annotation.notes)
            else:
                data = provider_yaml(members, header, annotation.notes)
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
        "documents": {path: sha256(data) for path, data in sorted(documents.items())},
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return files
