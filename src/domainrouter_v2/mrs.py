"""MRS：把 domain 与 ipcidr 规则文件编译为 Mihomo 的二进制规则集。

编码直接交给固定版本 Mihomo 自带的 ``convert-ruleset``（rules/provider/mrs_converter.go），
不在 Python 中重新实现格式：MRS 是 zstd 压缩的内核索引结构，由内核自己写出最可靠。
输入就是刚生成的 YAML 文件（文件头与同行注释在解析时被忽略）；同一输入编译结果逐字节相同，
因此不破坏确定性构建。classical 没有 MRS 形式（Mihomo 只为 domain/ipcidr 实现了编码）。

MRS 文件与 YAML 同目录、同名，只是扩展名为 ``.mrs``；不含任何注释。
"""

from __future__ import annotations

import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from domainrouter_v2.planner import DOMAIN, IPCIDR
from domainrouter_v2.tools import ToolError, find_executable, load_specs

_BEHAVIOR = {DOMAIN.directory: DOMAIN.behavior, IPCIDR.directory: IPCIDR.behavior}


class MrsError(RuntimeError):
    """MRS 编译失败。"""


def mrs_path(yaml_path: str) -> str | None:
    """``clash-domain/X.yaml`` → ``clash-domain/X.mrs``；classical 返回 None。"""
    directory = yaml_path.split("/", 1)[0]
    if directory not in _BEHAVIOR or not yaml_path.endswith(".yaml"):
        return None
    return yaml_path.removesuffix(".yaml") + ".mrs"


def mihomo_executable(state: Path) -> Path:
    """tools prepare 准备的 Mihomo：Linux 解压为 ``mihomo``，Windows 为 ``mihomo-*.exe``。"""
    try:
        return find_executable(state, load_specs()["mihomo"], ["mihomo", "mihomo*.exe"])
    except ToolError as exc:
        raise MrsError(f"{exc}（output.mrs 需要它来编译 MRS）") from exc


def compile_mrs(files: dict[str, bytes], mihomo: Path) -> dict[str, bytes]:
    """编译 files 中全部 domain/ipcidr YAML，返回 {MRS 路径: 字节}。并行调用，互不依赖。"""
    jobs = {path: target for path in files if (target := mrs_path(path)) is not None}
    if not jobs:
        return {}
    with tempfile.TemporaryDirectory(prefix="dr2-mrs-") as tmp:
        root = Path(tmp)

        def convert(path: str) -> tuple[str, bytes]:
            source = root / path
            target = root / jobs[path]
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(files[path])
            behavior = _BEHAVIOR[path.split("/", 1)[0]]
            completed = subprocess.run(
                [str(mihomo), "convert-ruleset", behavior, "yaml", str(source), str(target)],
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0 or not target.exists():
                detail = completed.stderr.decode("utf-8", "replace").strip().splitlines()
                raise MrsError(f"{path} 编译失败：{detail[-1] if detail else '无输出'}")
            return jobs[path], target.read_bytes()

        with ThreadPoolExecutor() as pool:
            return dict(pool.map(convert, sorted(jobs)))
