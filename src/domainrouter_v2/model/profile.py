"""解析后的个人配置（``my.wei``）：合集、来源引用与 ``[Rules]`` 路由表。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from domainrouter_v2.diagnostics import SourceSpan
from domainrouter_v2.model.rule import Condition, Member


@dataclass(frozen=True, slots=True)
class LocalMember:
    """直接写在 my.wei 中的成员（自由行、显式规则、粘贴块条目、@site）。"""

    member: Member
    span: SourceSpan
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceRef:
    """一个需要下载的上游来源。同一 URL 与格式在不同位置引用时共享下载与解析结果。"""

    url: str
    format: str
    span: SourceSpan
    exclude_types: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.format} {self.url}"


@dataclass(slots=True)
class Collection:
    name: str
    span: SourceSpan
    items: list[LocalMember | SourceRef] = field(default_factory=list)

    @property
    def sources(self) -> list[SourceRef]:
        return [item for item in self.items if isinstance(item, SourceRef)]

    @property
    def locals(self) -> list[LocalMember]:
        return [item for item in self.items if isinstance(item, LocalMember)]


class RouteKind(StrEnum):
    COLLECTION = "collection"
    INLINE = "inline"
    MATCH = "match"


@dataclass(frozen=True, slots=True)
class RouteEntry:
    """``[Rules]`` 的一行。index 从 0 开始，即最终路由优先级。"""

    index: int
    kind: RouteKind
    target: str
    span: SourceSpan
    collection: str = ""
    condition: Condition | None = None

    @property
    def inline_text(self) -> str:
        """内联规则在 rulesets.toml 中的 ``[]`` 之后的文本。"""
        if self.kind is RouteKind.MATCH:
            return "MATCH"
        assert self.condition is not None
        return self.condition.render()


@dataclass(slots=True)
class Profile:
    collections: dict[str, Collection] = field(default_factory=dict)
    routes: list[RouteEntry] = field(default_factory=list)

    @property
    def referenced(self) -> set[str]:
        return {r.collection for r in self.routes if r.kind is RouteKind.COLLECTION}
