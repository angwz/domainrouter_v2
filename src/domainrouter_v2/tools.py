"""验证工具的显式准备：按 ``config/tools.lock.json`` 下载、校验摘要、安全解压。

只有 ``tools prepare`` 会联网下载工具；构建与验证只检查已准备的工具，缺失时明确失败，
不会隐式下载或换用其他版本（规范 §11.1、M06）。
"""

from __future__ import annotations

import gzip
import hashlib
import json
import platform
import shutil
import stat
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from domainrouter_v2.sources.net import make_transport

LOCK_PATH = Path(__file__).with_name("tools.lock.json")


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    version: str
    url: str
    sha256: str
    archive: str
    filename: str = ""


def current_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    if system not in {"windows", "linux"} or arch is None:
        raise ToolError(f"未登记的平台：{system}/{machine}")
    return f"{system}-{arch}"


def load_specs(lock_path: Path = LOCK_PATH, plat: str | None = None) -> dict[str, ToolSpec]:
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    target = plat or current_platform()
    specs: dict[str, ToolSpec] = {}
    for name, tool in data["tools"].items():
        entry = tool["platforms"].get(target) or tool["platforms"].get("any")
        if entry is None:
            raise ToolError(f"{name} 没有 {target} 平台的锁定条目")
        specs[name] = ToolSpec(
            name,
            tool["version"],
            entry["url"],
            entry["sha256"],
            entry["archive"],
            entry.get("filename", ""),
        )
    return specs


def tool_dir(state: Path, spec: ToolSpec) -> Path:
    return state / "tools" / f"{spec.name}-{spec.version}"


def prepare(state: Path, spec: ToolSpec) -> Path:
    """下载并解压到 ``<state>/tools/<name>-<version>/``；已准备且摘要一致时直接返回。"""
    target = tool_dir(state, spec)
    marker = target / ".prepared"
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == spec.sha256:
        return target
    with httpx.Client(transport=make_transport(), follow_redirects=True, timeout=300) as client:
        response = client.get(spec.url)
        response.raise_for_status()
        data = response.content
    digest = hashlib.sha256(data).hexdigest()
    if digest != spec.sha256:
        raise ToolError(f"{spec.name} 下载内容摘要不符：期望 {spec.sha256}，实际 {digest}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    archive = target.parent / f".{spec.name}-{spec.version}.download"
    archive.write_bytes(data)
    try:
        _extract(archive, target, spec)
    finally:
        archive.unlink()
    marker.write_text(spec.sha256 + "\n", encoding="utf-8")
    return target


def _extract(archive: Path, target: Path, spec: ToolSpec) -> None:
    root = target.resolve()

    def safe(name: str) -> Path:
        path = (root / name).resolve()
        if root not in path.parents and path != root:
            raise ToolError(f"归档成员试图写到目标目录之外：{name}")
        return path

    if spec.archive == "zip":
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                safe(member.filename)
            zf.extractall(root)
    elif spec.archive == "tar.gz":
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(root, filter="data")  # data 过滤器拒绝绝对路径、.. 与危险链接
    elif spec.archive == "raw":
        shutil.copyfile(archive, safe(spec.filename))
    elif spec.archive == "gz":
        executable = safe(spec.name)
        with gzip.open(archive) as source, executable.open("wb") as sink:
            shutil.copyfileobj(source, sink)
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    else:
        raise ToolError(f"未知归档格式：{spec.archive}")


def find_executable(state: Path, spec: ToolSpec, relative_candidates: list[str]) -> Path:
    """在已准备的目录中找到可执行文件；没准备时报错并提示命令。"""
    base = tool_dir(state, spec)
    if not (base / ".prepared").exists():
        raise ToolError(
            f"{spec.name} {spec.version} 尚未准备，请先运行 domainrouter_v2 tools prepare"
        )
    for candidate in relative_candidates:
        matches = sorted(base.glob(candidate))
        if matches:
            return matches[0]
    raise ToolError(f"在 {base} 中找不到 {spec.name} 可执行文件")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
