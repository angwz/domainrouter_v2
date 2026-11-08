"""把一次成功构建的产物整套放进 release 工作目录（allowlist，不递归复制整个 dist）。

只在规则或 TOML 有变化时改动 release 目录；内容未变时什么也不写，
调用方（每日工作流）据此跳过提交，不制造空提交（规范 A03）。
规则文件的 ``# UPDATED:`` 是该文件内容最后一次变化的时间：除时间外与已发布版本相同的文件
保留原字节不动，因此一次更新只会改动真正变化的文件。
本模块不执行任何 git 或网络操作：提交与推送由工作流完成。
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from domainrouter_v2.emit import stamp_updated, strip_updated
from domainrouter_v2.planner import PARTITIONS
from domainrouter_v2.report import RunReport

PUBLISHED_FILES = ("rulesets.toml", "groups.toml", "manifest.json")
REPORT_DIR = "reports"


def stage_release(release_dir: Path, files: dict[str, bytes], report: RunReport) -> bool:
    """返回是否改动了 release 目录。"""
    if not report.changed:
        return False
    release_dir.mkdir(parents=True, exist_ok=True)
    for partition in PARTITIONS:
        directory = release_dir / partition.directory
        if directory.is_dir():
            for stale in directory.glob("*.yaml"):
                if f"{partition.directory}/{stale.name}" not in files:
                    stale.unlink()
    reports = release_dir / REPORT_DIR
    if reports.exists():
        shutil.rmtree(reports)
    reports.mkdir()
    when = datetime.fromisoformat(report.generated_at)
    rule_dirs = {p.directory for p in PARTITIONS}
    for path, data in files.items():
        top = path.split("/", 1)[0]
        target = release_dir / path
        output = data
        if top in rule_dirs:
            if target.exists() and strip_updated(target.read_bytes()) == data:
                continue  # 内容未变：保留原文件及其更新时间
            output = stamp_updated(data, when)
        elif path not in PUBLISHED_FILES and top != REPORT_DIR:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
    (reports / "latest.md").write_bytes(report.to_markdown())
    (reports / "changes.json").write_bytes(report.to_json())
    return True
