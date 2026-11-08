"""来源格式适配器的公共结果类型。

每个适配器把一份已解码的文本转换为 ``ParseResult``：
- ``entries``：成功转换的成员（带行号与修复说明）；
- ``skipped``：合法但无法转换、或单行写法错误的条目——进入每日更新说明，不使整份来源失败；
- 整份内容无法按该格式理解时抛 ``SourceFormatError``，由来源层决定是否改用上次成功的副本。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domainrouter_v2.model.rule import Member


class SourceFormatError(Exception):
    """整份来源不符合声明/识别出的格式。"""


@dataclass(frozen=True, slots=True)
class Entry:
    member: Member
    line: int
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Skipped:
    line: int
    text: str
    reason: str
    invalid: bool = False  # True：写法错误；False：合法但无法转换


@dataclass(slots=True)
class ParseResult:
    format: str
    entries: list[Entry] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)

    def add(self, member: Member, line: int, notes: list[str] | tuple[str, ...] = ()) -> None:
        self.entries.append(Entry(member, line, tuple(notes)))

    def skip(self, line: int, text: str, reason: str, *, invalid: bool = False) -> None:
        self.skipped.append(Skipped(line, text, reason, invalid))


def iter_lines(text: str) -> list[tuple[int, str]]:
    """去掉 BOM，按任意换行切分，返回 (行号, 去除首尾空白的行)。"""
    return [(i, line.strip()) for i, line in enumerate(text.removeprefix("﻿").splitlines(), 1)]


def strip_comment_line(line: str, markers: tuple[str, ...]) -> bool:
    """空行或以注释标记开头的整行注释。"""
    return not line or line.startswith(markers)
