"""规则文件的来源标注：文件头的来源图例，与每条规则的同行注释。

每个文件只为实际出现的来源分配字母，按 my.wei 中的声明顺序编为 A、B、C……
同行注释的三部分（有则显示）：

    - '+.baidu.com'          # B C  覆盖 a.baidu.com B, tieba.baidu.com C 等 128 条
    - '+.example.com'        # 合并 example.com A, .example.com B

- 字母：该条规则原样出现在哪些来源中；
- 合并：它由哪些输入合成（本身不在任何来源中原样出现），最多列出 ``SHOWN_MERGED`` 条；
- 覆盖：被它完整包含而删去的输入，最多列出 ``SHOWN_COVERED`` 条；
超出的部分只计数。完整列表用 ``domainrouter_v2 explain --rule '<规则>'`` 查看（describe）。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlsplit

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.rule import Leaf, Member, render_member
from domainrouter_v2.provenance import HANDWRITTEN, ArtifactTrace, Trace

SHOWN_MERGED = 3
SHOWN_COVERED = 2
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True, slots=True)
class Annotation:
    legend: list[str]  # 文件头中的 ``SOURCE A: …`` 行
    notes: dict[Member, str]  # 每条规则的同行注释（不含 ``#``）


def annotate(members: list[Member], trace: ArtifactTrace) -> Annotation:
    used: set[str] = set()
    for member in members:
        item = trace.traces.get(member)
        if item is not None:
            used |= item.own
            used.update(label for _, labels in (*item.merged, *item.covered) for label in labels)
    ordered = [label for label in trace.labels if label in used]
    letters = {label: _letter(i) for i, label in enumerate(ordered)}
    names = _display_names(ordered)
    legend = [f"SOURCE {letters[label]}: {names[label]}" for label in ordered]

    notes: dict[Member, str] = {}
    for member in members:
        item = trace.traces.get(member)
        if item is not None:
            notes[member] = _note(member, item, letters)
    return Annotation(legend, notes)


def _note(output: Member, trace: Trace, letters: dict[str, str]) -> str:
    parts: list[str] = []
    if trace.own:
        parts.append(_refs(trace.own, letters))
    if trace.merged:
        parts.append("合并 " + _listing(output, trace.merged, letters, SHOWN_MERGED))
    if trace.covered:
        parts.append("覆盖 " + _listing(output, trace.covered, letters, SHOWN_COVERED))
    return "  ".join(parts)


def _listing(
    output: Member,
    entries: tuple[tuple[Member, frozenset[str]], ...],
    letters: dict[str, str],
    limit: int,
) -> str:
    ordered = sorted(entries, key=lambda entry: _order(entry[0]))
    shown = ordered[:limit]
    text = ", ".join(f"{_shown(output, m)} {_refs(labels, letters)}" for m, labels in shown)
    if len(ordered) > len(shown):
        text += f" 等 {len(ordered)} 条"
    return text


def _refs(labels: Iterable[str], letters: dict[str, str]) -> str:
    return " ".join(sorted((letters[label] for label in labels), key=lambda s: (len(s), s)))


def _shown(output: Member, member: Member) -> str:
    """被吸收的输入与输出同类型时只写载荷，例如 DOMAIN-KEYWORD 下写 ``googleapis``。"""
    if isinstance(member, Leaf) and isinstance(output, Leaf) and member.type == output.type:
        return member.payload
    return render_member(member)


def _order(member: Member) -> tuple[int, int, str]:
    """与规则文件相同的展示次序：域名从宽到窄，网段按地址，其余按文本。"""
    if isinstance(member, DomainPattern):
        return member.display_key()
    if isinstance(member, Network):
        return (member.version, member.first, str(member.prefix))
    return (0, 0, render_member(member))


def _letter(index: int) -> str:
    """A…Z、AA…AZ、BA……"""
    text = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        text = _ALPHABET[rest] + text
    return text


def _display_names(labels: list[str]) -> dict[str, str]:
    """来源的简短名称：作者或主机名 · 最后两级路径。简称重复时改用完整 URL。"""
    short = {label: _short(label) for label in labels}
    counts: dict[str, int] = {}
    for name in short.values():
        counts[name] = counts.get(name, 0) + 1
    return {label: name if counts[name] == 1 else label for label, name in short.items()}


def _short(label: str) -> str:
    if label == HANDWRITTEN:
        return HANDWRITTEN
    parts = urlsplit(label)
    segments = [s for s in parts.path.split("/") if s]
    owner = (
        segments[0] if parts.netloc == "raw.githubusercontent.com" and segments else parts.netloc
    )
    tail = "/".join(segments[-2:])
    return f"{owner} · {tail}" if tail else owner


def describe(output: Member, trace: Trace, path: str, groups: tuple[str, ...]) -> str:
    """一条输出规则的完整来历（explain --rule），来源写完整 URL。"""
    lines = [f"{render_member(output)}", f"  文件：{path} → {', '.join(groups)}"]
    lines.append("  原样来自：" + (", ".join(sorted(trace.own)) or "无（由合并生成）"))
    for title, entries in (("合并自", trace.merged), ("覆盖", trace.covered)):
        if not entries:
            continue
        lines.append(f"  {title}（{len(entries)} 条）：")
        for member, labels in sorted(entries, key=lambda entry: _order(entry[0])):
            lines.append(f"    {render_member(member)}  ← {', '.join(sorted(labels))}")
    return "\n".join(lines)
