"""来源快照：每个来源最近一次成功解析的规范化成员，以及健康状态。

快照是构建的唯一输入（构建本身不联网）。布局（``<state>/``）：
- ``sources/<id>.txt``：首行 ``# `` + JSON 元数据，其后每行一个成员：
  ``d <原生域名>``、``n <网段>``、``c <classical 规则>``，按文本排序，便于 git 增量存储；
- ``status.json``：每个来源的健康记录（连续失败次数、最近成功时间等）。

存的是规范化后的成员，不是上游原文：体积小、diff 清晰，且不在仓库中再分发原始文件。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network, parse_network
from domainrouter_v2.model.rule import Member, render_member
from domainrouter_v2.parse.rule_text import NoResolvePolicy, convert_condition

SNAPSHOT_VERSION = 1


def source_id(url: str, fmt: str, exclude_types: tuple[str, ...] = ()) -> str:
    key = "\x00".join((fmt, url, ",".join(exclude_types)))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def encode_member(member: Member) -> str:
    if isinstance(member, DomainPattern):
        return "d " + member.to_native()
    if isinstance(member, Network):
        return "n " + str(member)
    return "c " + render_member(member)


def decode_member(line: str) -> Member:
    tag, _, text = line.partition(" ")
    if tag == "d":
        return DomainPattern.parse_native(text)
    if tag == "n":
        return parse_network(text).network
    if tag == "c":
        # 快照中的条件已规范化：按原样保留参数，不再套用策略
        return convert_condition(text, NoResolvePolicy.KEEP).member
    raise ValueError(f"无法识别的快照行：{line!r}")


@dataclass(slots=True)
class SnapshotMeta:
    url: str
    format: str
    detected_format: str
    raw_sha256: str
    fetched_at: str
    entries: int
    skipped: int
    invalid: int
    version: int = SNAPSHOT_VERSION


@dataclass(slots=True)
class Snapshot:
    meta: SnapshotMeta
    lines: list[str]  # 已编码、已排序、已去重

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256("\n".join(self.lines).encode("utf-8")).hexdigest()

    def members(self) -> list[Member]:
        return [decode_member(line) for line in self.lines]


@dataclass(slots=True)
class SourceStatus:
    url: str
    format: str
    last_attempt: str = ""
    last_success: str = ""
    consecutive_failures: int = 0
    first_failure: str = ""
    last_error: str = ""
    etag: str = ""
    last_modified: str = ""
    raw_sha256: str = ""


@dataclass(slots=True)
class StateStore:
    root: Path
    statuses: dict[str, SourceStatus] = field(default_factory=dict)

    @classmethod
    def open(cls, root: Path) -> StateStore:
        store = cls(root)
        path = root / "status.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            store.statuses = {k: SourceStatus(**v) for k, v in data.get("sources", {}).items()}
        return store

    def snapshot_path(self, sid: str) -> Path:
        return self.root / "sources" / f"{sid}.txt"

    def load(self, sid: str) -> Snapshot | None:
        path = self.snapshot_path(sid)
        if not path.exists():
            return None
        header, _, body = path.read_text(encoding="utf-8").partition("\n")
        meta = SnapshotMeta(**json.loads(header.removeprefix("# ")))
        return Snapshot(meta, [line for line in body.split("\n") if line])

    def save(self, sid: str, snapshot: Snapshot) -> None:
        path = self.snapshot_path(sid)
        path.parent.mkdir(parents=True, exist_ok=True)
        header = "# " + json.dumps(asdict(snapshot.meta), ensure_ascii=False, sort_keys=True)
        _write_text(path, "\n".join([header, *snapshot.lines]) + "\n")

    def save_statuses(self) -> None:
        data = {
            "schema_version": 1,
            "sources": {k: asdict(v) for k, v in sorted(self.statuses.items())},
        }
        self.root.mkdir(parents=True, exist_ok=True)
        _write_text(
            self.root / "status.json",
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )


def make_snapshot(meta: SnapshotMeta, members: list[Member]) -> Snapshot:
    lines = sorted({encode_member(m) for m in members})
    return Snapshot(meta, lines)


def _write_text(path: Path, text: str) -> None:
    """先写临时文件再替换，避免中断时留下半个快照。"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    tmp.replace(path)
