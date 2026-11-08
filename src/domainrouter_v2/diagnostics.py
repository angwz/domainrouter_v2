"""诊断信息：稳定代码、级别、位置和可执行的修正提示。

诊断是引擎与用户之间唯一的错误通道：解析、规范化和规划都只产生诊断，不打印、不吞掉。
CLI 与报告从同一份诊断列表渲染。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Level(StrEnum):
    INFO = "info"  # 明确的修复或化简
    WARNING = "warning"  # 不影响已确定语义
    ERROR = "error"  # 无法唯一解释或无法输出；正式构建必须失败


class Code(StrEnum):
    # 输入与解析
    PARSE_AMBIGUOUS = "E_PARSE_AMBIGUOUS"
    PARSE_SYNTAX = "E_PARSE_SYNTAX"
    RULE_TYPE_UNKNOWN = "E_RULE_TYPE_UNKNOWN"
    TARGET_UNSUPPORTED = "E_TARGET_UNSUPPORTED"
    YAML_STRUCTURE = "E_YAML_STRUCTURE"
    # 路由与组
    ROUTE_REFERENCE = "E_ROUTE_REFERENCE"
    ROUTE_FALLBACK = "E_ROUTE_FALLBACK"
    GROUP_REFERENCE = "E_GROUP_REFERENCE"
    GROUP_CYCLE = "E_GROUP_CYCLE"
    GROUP_INVALID = "E_GROUP_INVALID"
    EMPTY_COLLECTION = "E_EMPTY_COLLECTION"
    BACKEND_LOSSY = "E_BACKEND_LOSSY"
    PROVIDER_NAME_COLLISION = "E_PROVIDER_NAME_COLLISION"
    # 来源
    SOURCE_FETCH = "E_SOURCE_FETCH"
    SOURCE_FORMAT = "E_SOURCE_FORMAT"
    SNAPSHOT_MISSING = "E_SNAPSHOT_MISSING"
    # 配置与输出
    CONFIG = "E_CONFIG"
    OUTPUT_PATH = "E_OUTPUT_PATH"
    VERIFY_MISMATCH = "E_VERIFY_MISMATCH"
    # 警告
    SOURCE_STALE = "W_SOURCE_STALE"
    SOURCE_POLICY_IGNORED = "W_SOURCE_POLICY_IGNORED"
    RULE_SKIPPED = "W_RULE_SKIPPED"
    REPAIRED = "W_REPAIRED"
    UNREFERENCED_COLLECTION = "W_UNREFERENCED_COLLECTION"
    RULESET_LIMIT = "W_RULESET_LIMIT"
    DUPLICATE_SECTION = "W_DUPLICATE_SECTION"
    BROAD_RULE = "W_BROAD_RULE"
    BROAD_FILTERED = "W_BROAD_FILTERED"
    TRACE_GAP = "W_TRACE_GAP"
    # 信息
    NORMALIZED = "I_NORMALIZED"
    DEDUPLICATED = "I_DEDUPLICATED"
    COVERED = "I_COVERED"
    MERGED = "I_MERGED"


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """输入中的位置。origin 为项目相对路径或稳定来源 ID，line 从 1 开始。"""

    origin: str
    line: int
    text: str = ""

    def __str__(self) -> str:
        return f"{self.origin}:{self.line}"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: Code
    level: Level
    message: str
    span: SourceSpan | None = None
    hint: str = ""

    def render(self) -> str:
        where = f"{self.span}: " if self.span else ""
        tail = f"\n  提示：{self.hint}" if self.hint else ""
        return f"{where}{self.level.value}[{self.code.value}] {self.message}{tail}"


def error(code: Code, message: str, span: SourceSpan | None = None, hint: str = "") -> Diagnostic:
    return Diagnostic(code, Level.ERROR, message, span, hint)


def warning(code: Code, message: str, span: SourceSpan | None = None, hint: str = "") -> Diagnostic:
    return Diagnostic(code, Level.WARNING, message, span, hint)


def info(code: Code, message: str, span: SourceSpan | None = None, hint: str = "") -> Diagnostic:
    return Diagnostic(code, Level.INFO, message, span, hint)


def has_errors(diagnostics: list[Diagnostic]) -> bool:
    return any(d.level is Level.ERROR for d in diagnostics)
