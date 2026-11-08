"""安装包内容（规范 O02、G01）：只含包内代码与必要数据，不含个人输入、缓存或测试资料。"""

from __future__ import annotations

import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
ALLOWED_DATA = {
    "domainrouter_v2/py.typed",
    "domainrouter_v2/tools.lock.json",
    "domainrouter_v2/data/broad_keywords.txt",
    "domainrouter_v2/data/public_suffix_icann.txt",
}


def test_project_identity() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == "domainrouter_v2"
    assert project["scripts"] == {"domainrouter_v2": "domainrouter_v2.cli:main"}
    assert (ROOT / "src" / "domainrouter_v2" / "__init__.py").exists()
    assert (ROOT / "config" / "domainrouter_v2.toml").exists()


@pytest.mark.skipif(shutil.which("uv") is None, reason="需要 uv")
def test_wheel_contents(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    wheel = next(tmp_path.glob("domainrouter_v2-*.whl"))
    names = [n for n in zipfile.ZipFile(wheel).namelist() if not n.endswith("/")]
    package = [n for n in names if not n.startswith("domainrouter_v2-")]
    assert package, "wheel 中没有包文件"
    for name in package:
        assert name.startswith("domainrouter_v2/"), name
        assert name.endswith(".py") or name in ALLOWED_DATA, name
        assert "__pycache__" not in name, name
    forbidden = ("my.wei", "groups.toml", ".cache", "tests/", "examples/", "status.json")
    assert not [n for n in names if any(f in n for f in forbidden)]


def test_example_has_no_private_material() -> None:
    """公共示例只使用保留的示例域名与文档地址段，不含订阅或凭据。"""
    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "examples" / "minimal").rglob("*")
        if p.is_file()
        and p.suffix in {".wei", ".toml", ""}
        and "dist" not in p.parts
        and ".cache" not in p.parts
    )
    for marker in ("token", "password", "secret", "subscribe", "angwz"):
        assert marker not in text.lower()
