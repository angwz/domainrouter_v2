"""每次运行的更新说明：来源健康、规则增删、未转换条目与优化统计。

数据只来自本次构建结果与快照目录，不依赖抓取进程，因此 fetch、build、publish 可以分开运行。
变化基于规范化后的集合比较（新增/删除），不做文本 diff。
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from domainrouter_v2.build import BROAD_REPORT, BuildResult, inline_dns_routes
from domainrouter_v2.config import Config
from domainrouter_v2.emit import read_payload
from domainrouter_v2.planner import PARTITIONS

MAX_LISTED = 200


@dataclass(slots=True)
class FileChange:
    path: str
    before: int
    after: int
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)


def diff_files(previous_dir: Path | None, files: dict[str, bytes]) -> list[FileChange]:
    changes: list[FileChange] = []
    previous_paths: set[str] = set()
    if previous_dir is not None:
        for partition in PARTITIONS:
            base = previous_dir / partition.directory
            if base.is_dir():
                previous_paths |= {f"{partition.directory}/{p.name}" for p in base.glob("*.yaml")}
    for path in sorted(previous_paths | {p for p in files if p.endswith(".yaml")}):
        old = (
            read_payload((previous_dir / path).read_bytes())
            if previous_dir is not None and path in previous_paths
            else []
        )
        new = read_payload(files[path]) if path in files else []
        old_set, new_set = set(old), set(new)
        changes.append(
            FileChange(
                path,
                len(old),
                len(new),
                sorted(new_set - old_set),
                sorted(old_set - new_set),
            )
        )
    return changes


def skipped_summary(config: Config, result: BuildResult) -> list[tuple[str, int, str]]:
    """(原因, 数量, 示例)：汇总当前快照对应的未转换条目。"""
    reasons: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for source in result.sources:
        path = config.state / "sources" / f"{source.sid}.skipped.txt"
        if source.snapshot is None or not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t", 3)
            if len(parts) != 4:
                continue
            reason = _reason_key(parts[3])
            reasons[reason] += 1
            examples.setdefault(reason, parts[2])
    return [(reason, count, examples[reason]) for reason, count in reasons.most_common()]


def _reason_key(reason: str) -> str:
    """把带具体值的原因归并成类别，例如「未登记的规则类型 'X'」。"""
    if reason.startswith("未登记的规则类型"):
        return reason
    return reason.split("：", 1)[0] if "：" in reason and len(reason) > 60 else reason


@dataclass(slots=True)
class RunReport:
    generated_at: str
    generation: str
    changes: list[FileChange]
    toml_changed: bool
    sources: list[dict[str, Any]]
    skipped: list[tuple[str, int, str]]
    optimization: list[dict[str, Any]]
    dns_routes: list[str]
    stale_days: int
    broad_filtered: list[dict[str, str]] = field(default_factory=list)
    broad_new: list[dict[str, str]] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.toml_changed or any(c.changed for c in self.changes)

    def to_json(self) -> bytes:
        data = {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "generation": self.generation,
            "changed": self.changed,
            "files": [
                {
                    "path": c.path,
                    "before": c.before,
                    "after": c.after,
                    "added": c.added,
                    "removed": c.removed,
                }
                for c in self.changes
            ],
            "sources": self.sources,
            "skipped": [{"reason": r, "count": n, "example": e} for r, n, e in self.skipped],
            "optimization": self.optimization,
            "dns_routes": self.dns_routes,
            "broad": {"filtered": self.broad_filtered, "new": self.broad_new},
        }
        return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    def to_markdown(self) -> bytes:
        lines = ["# 规则更新说明", ""]
        lines += [
            f"- 生成时间（UTC）：{self.generated_at}",
            f"- generation：`{self.generation[:16]}`",
        ]
        lines.append(
            f"- 结果：{'有变化，已更新发布文件' if self.changed else '内容未变化，未提交新版本'}"
        )
        lines.append("")
        dead = [s for s in self.sources if s["failed_days"] >= self.stale_days]
        failing = [s for s in self.sources if s["failures"]]
        if dead:
            lines += ["## ⚠️ 可能已失效的来源", ""]
            lines.append(
                f"以下来源已连续失败 {self.stale_days} 天以上，仍在使用上次成功的内容。"
                "如果不再需要，请从 my.wei 中删除。"
            )
            lines.append("")
            lines += [f"- {s['url']}（失败 {s['failed_days']} 天：{s['error']}）" for s in dead]
            lines.append("")
        lines += self._broad_section()
        lines += ["## 来源", ""]
        fresh = sum(1 for s in self.sources if not s["failures"])
        lines.append(
            f"共 {len(self.sources)} 个：正常 {fresh} 个，失败 {len(failing)} 个（使用旧副本）。"
        )
        if failing:
            lines += ["", "| 来源 | 连续失败 | 原因 |", "| --- | --- | --- |"]
            lines += [f"| {s['url']} | {s['failures']} 次 | {s['error']} |" for s in failing]
        lines += ["", "## 规则变化", ""]
        changed = [c for c in self.changes if c.changed]
        if not changed:
            lines.append("规则文件内容没有变化。")
        else:
            lines += ["| 文件 | 条目 | 新增 | 删除 |", "| --- | --- | --- | --- |"]
            lines += [
                f"| `{c.path}` | {c.before} → {c.after} | {len(c.added)} | {len(c.removed)} |"
                for c in changed
            ]
            for c in changed:
                lines += ["", "<details>", f"<summary><code>{c.path}</code></summary>", ""]
                lines += _listing("新增", c.added) + _listing("删除", c.removed)
                lines += ["</details>"]
        if self.skipped:
            lines += ["", "## 未转换的上游条目", ""]
            lines += ["| 原因 | 数量 | 示例 |", "| --- | --- | --- |"]
            lines += [f"| {r} | {n} | `{e}` |" for r, n, e in self.skipped]
        lines += ["", "## 优化统计", ""]
        lines += [
            "| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        lines += [
            f"| {o['collections']} | {o['input']} | {o['output']} | {o['duplicates']} | "
            f"{o['covered']} | {o['merged']} |"
            for o in self.optimization
        ]
        if self.dns_routes:
            lines += ["", "## 会触发 DNS 解析的手写内联规则", ""]
            lines += ["按原样保留（未加 no-resolve）："]
            lines += [f"- `{route}`" for route in self.dns_routes]
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _broad_section(self) -> list[str]:
        """宽泛规则放在来源之前：过滤与新增都需要用户留意。完整清单见 broad-rules.md。"""
        lines = ["## 宽泛规则", ""]
        lines.append(
            f"本次过滤上游规则 {len(self.broad_filtered)} 条，"
            f"新发布的宽泛规则 {len(self.broad_new)} 条。"
            "完整清单见 [broad-rules.md](broad-rules.md)。"
        )
        if self.broad_filtered:
            lines += ["", "| 已过滤 | 原因 | 合集 | 来源 |", "| --- | --- | --- | --- |"]
            lines += [
                f"| `{f['rule']}` | {f['reason']} | {f['collection']} | {f['source']} |"
                for f in self.broad_filtered[:MAX_LISTED]
            ]
        if self.broad_new:
            lines += ["", "| 新发布 | 说明 | 文件 |", "| --- | --- | --- |"]
            lines += [
                f"| `{n['rule']}` | {n['reason']} | `{n['path']}` |"
                for n in self.broad_new[:MAX_LISTED]
            ]
        return [*lines, ""]


def _listing(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    shown = items[:MAX_LISTED]
    out = [f"{title}（{len(items)}）：", "", "```text", *shown, "```"]
    if len(items) > MAX_LISTED:
        out.append(f"……其余 {len(items) - MAX_LISTED} 条见 changes.json")
    out.append("")
    return out


def make_report(
    config: Config,
    result: BuildResult,
    previous_dir: Path | None,
    now: datetime,
) -> RunReport:
    assert result.plan is not None and result.profile is not None
    manifest = json.loads(result.files["manifest.json"])
    changes = diff_files(previous_dir, result.files)
    toml_changed = any(
        previous_dir is None
        or not (previous_dir / name).exists()
        or (previous_dir / name).read_bytes() != result.files[name]
        for name in ("rulesets.toml", "groups.toml", BROAD_REPORT)
    )
    sources = []
    for source in result.sources:
        failed_days = 0
        if source.first_failure:
            first = datetime.fromisoformat(source.first_failure)
            failed_days = (now - first).days
        sources.append(
            {
                "url": source.ref.url,
                "format": source.ref.format,
                "entries": source.snapshot.meta.entries if source.snapshot else 0,
                "failures": source.consecutive_failures,
                "failed_days": failed_days,
                "error": source.last_error,
            }
        )
    optimization = []
    for artifact in result.plan.artifacts.values():
        output = len(artifact.domains) + len(artifact.networks) + len(artifact.conditions)
        de, ce = artifact.domain_events, artifact.classical_events
        optimization.append(
            {
                "collections": " + ".join(artifact.collections),
                "input": artifact.input_count,
                "output": output,
                "duplicates": de.duplicates + ce.duplicates,
                "covered": len(de.covered) + len(ce.covered),
                "merged": sum(len(v) for v in de.merged.values())
                + sum(len(v) for v in ce.merged.values())
                + max(0, artifact.network_input - len(artifact.networks)),
            }
        )
    added = {(c.path, item) for c in changes for item in c.added}
    broad_new = [
        {"path": listing.path, "rule": rule.text, "reason": rule.verdict.reason}
        for listing in result.broad
        for rule in listing.rules
        if (listing.path, rule.text) in added
    ]
    broad_filtered = [
        {"rule": f.text, "reason": f.verdict.reason, "collection": f.collection, "source": f.source}
        for f in sorted(result.filtered, key=lambda f: (f.collection, f.text, f.source))
    ]
    return RunReport(
        generated_at=now.isoformat(timespec="seconds"),
        generation=manifest["generation"],
        changes=changes,
        toml_changed=toml_changed,
        sources=sources,
        skipped=skipped_summary(config, result),
        optimization=optimization,
        dns_routes=inline_dns_routes(result.profile),
        stale_days=config.fetch.stale_warning_days,
        broad_filtered=broad_filtered,
        broad_new=broad_new,
    )
