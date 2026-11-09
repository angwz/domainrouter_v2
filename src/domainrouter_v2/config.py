"""构建配置 ``config/domainrouter_v2.toml`` 的读取与严格校验。

相对路径一律以 ``project_root`` 解析，``project_root`` 以配置文件所在目录为基准，
从不依赖调用时的工作目录。发布地址通过 URL 结构校验，不用字符串拼接猜测。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

SCHEMA_VERSION = 1


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FetchConfig:
    max_workers: int = 8
    max_attempts: int = 3
    connect_timeout_seconds: float = 10
    read_timeout_seconds: float = 30
    total_timeout_seconds: float = 120
    max_response_bytes: int = 32 * 1024 * 1024
    shrink_threshold: float = 0.5  # 条目数比上次成功少于该比例视为异常
    max_invalid_ratio: float = 0.2  # 写法错误的行超过该比例视为格式异常
    stale_warning_days: int = 7


@dataclass(frozen=True, slots=True)
class Config:
    path: Path
    project_root: Path
    rules: Path
    groups: Path
    state: Path
    output: Path
    base_url: str
    interval_seconds: int
    mrs: bool  # 同时发布 domain/ipcidr 的 MRS（需要 tools prepare 准备的 Mihomo）
    allow_empty_collections: frozenset[str]
    fetch: FetchConfig

    def resource_url(self, relative: str) -> str:
        """发布基址 + 受控相对路径（逐段百分号编码）。"""
        segments = [quote(part, safe="") for part in relative.split("/")]
        return self.base_url.rstrip("/") + "/" + "/".join(segments)

    @property
    def repository_url(self) -> str:
        """base_url 为 ``https://raw.githubusercontent.com/<owner>/<repo>/<ref>`` 时，
        返回仓库主页，用于规则文件头的 REPO；其他发布地址返回空串（不猜测）。"""
        parts = urlsplit(self.base_url)
        segments = [s for s in parts.path.split("/") if s]
        if parts.netloc != "raw.githubusercontent.com" or len(segments) < 3:
            return ""
        return f"https://github.com/{segments[0]}/{segments[1]}"


_ALLOWED = {
    "": {"schema_version", "project_root", "paths", "output", "policy", "fetch"},
    "paths": {"rules", "groups", "state"},
    "output": {"directory", "base_url", "interval_seconds", "mrs"},
    "policy": {"allow_empty_collections"},
    "fetch": set(FetchConfig.__dataclass_fields__),
}


def load_config(path: Path) -> Config:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"找不到配置文件：{path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}：TOML 语法错误：{exc}") from exc
    return parse_config(data, path)


def parse_config(data: dict[str, Any], path: Path) -> Config:
    _check_keys(data, "")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ConfigError(f"schema_version 必须为 {SCHEMA_VERSION}")
    root = (path.parent / str(data.get("project_root", ".."))).resolve()
    paths = _table(data, "paths")
    output = _table(data, "output")
    policy = _table(data, "policy")
    fetch_table = _table(data, "fetch")

    def resolve(value: Any, key: str) -> Path:
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{key} 必须是非空字符串")
        return (root / value).resolve()

    rules = resolve(paths.get("rules", "my.wei"), "paths.rules")
    groups = resolve(paths.get("groups", "subconverter_config/groups.toml"), "paths.groups")
    state = resolve(paths.get("state", ".cache/domainrouter_v2"), "paths.state")
    out = resolve(output.get("directory", "dist"), "output.directory")
    _check_output(out, root, (rules, groups, state))

    base_url = output.get("base_url")
    if not isinstance(base_url, str):
        raise ConfigError("output.base_url 必须填写")
    _check_base_url(base_url)
    interval = output.get("interval_seconds", 21600)
    if not isinstance(interval, int) or isinstance(interval, bool) or interval <= 0:
        raise ConfigError("output.interval_seconds 必须是正整数")

    mrs = output.get("mrs", False)
    if not isinstance(mrs, bool):
        raise ConfigError("output.mrs 必须是 true 或 false")
    allow_empty = policy.get("allow_empty_collections", [])
    if not isinstance(allow_empty, list) or not all(isinstance(x, str) for x in allow_empty):
        raise ConfigError("policy.allow_empty_collections 必须是字符串数组")

    fetch = _fetch_config(fetch_table)
    return Config(
        path=path.resolve(),
        project_root=root,
        rules=rules,
        groups=groups,
        state=state,
        output=out,
        base_url=base_url,
        interval_seconds=interval,
        mrs=mrs,
        allow_empty_collections=frozenset(allow_empty),
        fetch=fetch,
    )


def _table(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"[{name}] 必须是表")
    _check_keys(value, name)
    return value


def _check_keys(table: dict[str, Any], name: str) -> None:
    unknown = set(table) - _ALLOWED[name]
    if unknown:
        where = f"[{name}]" if name else "顶层"
        raise ConfigError(f"{where} 含未知字段：{', '.join(sorted(unknown))}")


def _fetch_config(table: dict[str, Any]) -> FetchConfig:
    defaults = FetchConfig()
    values: dict[str, Any] = {}
    for key in FetchConfig.__dataclass_fields__:
        value = table.get(key, getattr(defaults, key))
        if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
            raise ConfigError(f"fetch.{key} 必须是正数")
        values[key] = value
    for key in ("shrink_threshold", "max_invalid_ratio"):
        if values[key] >= 1:
            raise ConfigError(f"fetch.{key} 必须在 0 与 1 之间")
    for key in ("max_workers", "max_attempts", "max_response_bytes", "stale_warning_days"):
        if not isinstance(values[key], int):
            raise ConfigError(f"fetch.{key} 必须是整数")
    return FetchConfig(**values)


def _check_base_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ConfigError("output.base_url 必须是 http(s) 地址")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ConfigError("output.base_url 不能包含用户信息、查询参数或片段")
    if "YOUR_OWNER" in url:
        raise ConfigError("output.base_url 仍是占位符 YOUR_OWNER，请替换为实际发布地址")


def _check_output(out: Path, root: Path, inputs: tuple[Path, ...]) -> None:
    """输出目录不能是项目根、源码目录、缓存目录或任何输入的祖先（规范 §11.1）。"""
    forbidden = [root, root / "src", root / "docs", *inputs]
    for path in forbidden:
        if out == path or out in path.parents:
            raise ConfigError(f"output.directory 不能是 {path} 或其祖先目录")
