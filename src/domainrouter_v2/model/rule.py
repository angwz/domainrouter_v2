"""规则条件与合集成员。

一个合集成员属于三种分区之一：
- ``DomainPattern``：进入 domain 集合；
- ``Network``：目标地址，进入 ipcidr 集合；
- ``Condition``：其余条件，进入 classical（逐条求值）。

``Condition`` 用树表示逻辑规则，禁止用逗号拼接的字符串代替树（规范 §7.3）。
"""

from __future__ import annotations

from dataclasses import dataclass

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network


@dataclass(frozen=True, slots=True, order=True)
class Leaf:
    """一个非逻辑规则条件，``type`` 为 Mihomo 规范类型名，``params`` 如 ``("no-resolve",)``。"""

    type: str
    payload: str
    params: tuple[str, ...] = ()

    def render(self) -> str:
        return ",".join((self.type, self.payload, *self.params))


@dataclass(frozen=True, slots=True, order=True)
class Logic:
    """AND / OR / NOT。子条件顺序即求值顺序，不做交换律或德摩根改写。"""

    op: str
    children: tuple[Condition, ...]

    def render(self) -> str:
        inner = ",".join(f"({child.render()})" for child in self.children)
        return f"{self.op},({inner})"


type Condition = Leaf | Logic
type Member = DomainPattern | Network | Condition


def render_member(member: Member) -> str:
    """成员在可读报告与 provider 文件中的文本形式。"""
    if isinstance(member, DomainPattern):
        return member.to_native()
    if isinstance(member, Network):
        return str(member)
    return member.render()
