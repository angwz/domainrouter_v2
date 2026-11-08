"""Mihomo 原生域名模式的规范表示与精确包含判定。

原生语法（domain behavior 的 rule-provider，以及 Mihomo trie）：
- ``a.com`` 精确；``*`` 匹配恰好一个完整非空标签；
- ``+.a.com`` 自身及任意层子域；``.a.com`` 至少一层子域（不含自身）。

规范表示 ``(min_labels, max_labels, literals)``：
- 主机名按标签计数，``max_labels`` 为 ``None`` 表示无上界；
- ``literals`` 为「从右端 0 开始的位置 → 固定标签」，未列出的位置可以是任意非空标签。

同一个匹配语言只有唯一的规范表示，因此 ``DomainPattern`` 可以直接作为去重键；
``+.*.a.com`` 与 ``.a.com`` 规范化后相同。

包含判定（规范 1.5 §9.3）：在「非空标签串」论域上，L(P) ⊆ L(Q) 当且仅当
1. Len(P) ⊆ Len(Q)；
2. Q 的每个 (位置, literal) 在 P 的同一位置有完全相同的 literal。
单对判定成本 O(|Lit(Q)|)。
"""

from __future__ import annotations

from dataclasses import dataclass

import idna

MAX_HOST_LENGTH = 253
MAX_LABEL_LENGTH = 63
# 已转换为 ASCII 的字面标签允许的字符：LDH 加下划线（_dmarc 等真实存在）。
_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
_UNBOUNDED_SORT = 1 << 30


class DomainError(ValueError):
    """输入不是合法的原生域名模式。消息面向用户，可直接放进诊断。"""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.hint = hint


def normalize_label(label: str) -> str:
    """把一个字面标签规范化为 ASCII 小写 A-label。

    非 ASCII 标签按 UTS #46 非过渡映射转换（idna 库）；ASCII 标签只做小写，
    不用 casefold 扩大等价类，也不把含下划线的标签送进 IDNA（会被拒绝）。
    """
    if not label:
        raise DomainError("域名含空标签")
    if label.isascii():
        out = label.lower()
    else:
        try:
            out = idna.encode(label, uts46=True, transitional=False).decode("ascii")
        except idna.IDNAError as exc:
            raise DomainError(f"无法转换为 IDNA A-label：{label!r}（{exc}）") from exc
        if "." in out:
            # UTS #46 映射可能把全角句点等字符映射成分隔符，不能让它引入额外层级
            raise DomainError(f"标签 {label!r} 经 IDNA 映射后包含分隔符")
    if len(out) > MAX_LABEL_LENGTH:
        raise DomainError(f"标签超过 {MAX_LABEL_LENGTH} 个字符：{out!r}")
    if not set(out) <= _LABEL_CHARS:
        bad = "".join(sorted(set(out) - _LABEL_CHARS))
        raise DomainError(f"标签 {out!r} 含不允许的字符 {bad!r}")
    if out.startswith("-") or out.endswith("-"):
        raise DomainError(f"标签 {out!r} 以连字符开头或结尾")
    return out


def normalize_host(text: str) -> str:
    """规范化一个不含通配的字面主机名（小写、A-label）。末尾点由调用方先行处理。"""
    host = ".".join(normalize_label(label) for label in text.split("."))
    if len(host) > MAX_HOST_LENGTH:
        raise DomainError(f"域名超过 {MAX_HOST_LENGTH} 个字符")
    return host


@dataclass(frozen=True, slots=True, order=True)
class DomainPattern:
    """一个原生域名模式的规范表示。字段含义见模块文档。"""

    min_labels: int
    max_labels: int | None
    literals: tuple[tuple[int, str], ...]

    def __post_init__(self) -> None:
        # 不变量：长度区间非空；literal 位置升序、唯一，且都落在最少层数之内。
        if self.min_labels < 1:
            raise ValueError("min_labels 必须 ≥ 1")
        if self.max_labels is not None and self.max_labels < self.min_labels:
            raise ValueError("max_labels 小于 min_labels")
        positions = [pos for pos, _ in self.literals]
        if positions != sorted(set(positions)) or (positions and positions[-1] >= self.min_labels):
            raise ValueError("literals 位置无效")

    # ---- 构造 ----

    @classmethod
    def exact(cls, host: str) -> DomainPattern:
        """精确主机名（host 须已规范化）。"""
        labels = host.split(".")
        return cls(len(labels), len(labels), _literals_of(labels))

    @classmethod
    def suffix(cls, host: str) -> DomainPattern:
        """自身及全部子域，等价于 ``+.host`` / DOMAIN-SUFFIX。"""
        labels = host.split(".")
        return cls(len(labels), None, _literals_of(labels))

    @classmethod
    def parse_native(cls, text: str) -> DomainPattern:
        """解析 Mihomo 原生模式文本，同时规范化字面标签。非法输入抛 DomainError。"""
        if not text:
            raise DomainError("空域名")
        if any(ch.isspace() for ch in text):
            raise DomainError(f"域名含空白：{text!r}")
        body = text
        unbounded = False
        extra = 0
        if body.startswith("+."):
            body, unbounded = body[2:], True
        elif body.startswith("."):
            body, unbounded, extra = body[1:], True, 1
        if not body:
            raise DomainError(f"缺少域名主体：{text!r}")
        if body.endswith("."):
            raise DomainError(f"域名末尾有点：{text!r}", hint="去掉末尾的根点")
        labels = body.split(".")
        literals: list[tuple[int, str]] = []
        for pos, label in enumerate(reversed(labels)):
            if label == "*":
                continue
            if "+" in label:
                raise DomainError(
                    f"'+' 只能作为最左侧的独立前缀 '+.'：{text!r}",
                    hint="使用 '+.example.com' 表示自身及全部子域",
                )
            if "*" in label or "?" in label:
                raise DomainError(
                    f"原生模式只支持完整标签通配 '*'：{text!r}",
                    hint="局部通配请改用显式规则 DOMAIN-WILDCARD,…",
                )
            literals.append((pos, normalize_label(label)))
        fixed = len(labels)
        if sum(len(lab) for _, lab in literals) + fixed - 1 > MAX_HOST_LENGTH:
            raise DomainError(f"域名超过 {MAX_HOST_LENGTH} 个字符")
        return cls(fixed + extra, None if unbounded else fixed, tuple(literals))

    # ---- 关系与变换 ----

    def with_subdomain_closure(self) -> DomainPattern:
        """原匹配结果再加上任意层子域：长度上界改为无穷，下界与 literal 不变。"""
        return DomainPattern(self.min_labels, None, self.literals)

    def covers(self, other: DomainPattern) -> bool:
        """当且仅当 L(other) ⊆ L(self)。见模块文档的充要条件。"""
        if other.min_labels < self.min_labels:
            return False
        if self.max_labels is not None and (
            other.max_labels is None or other.max_labels > self.max_labels
        ):
            return False
        theirs = dict(other.literals)
        return all(theirs.get(pos) == label for pos, label in self.literals)

    def union(self, other: DomainPattern) -> DomainPattern | None:
        """若两个模式的并集仍是单个原生模式则返回它，否则 None。

        只合并 literal 表完全相同、长度区间相交或相邻的情形（规范 §9.3 第 4 步），
        例如 ``a.com`` ∪ ``.a.com`` = ``+.a.com``。不填补缺失层级，不推断新的 ANY。
        """
        if self.literals != other.literals:
            return None
        first, second = sorted((self, other), key=lambda p: p.min_labels)
        if first.max_labels is not None and second.min_labels > first.max_labels + 1:
            return None  # 区间之间有空隙
        if first.max_labels is None or second.max_labels is None:
            upper = None
        else:
            upper = max(first.max_labels, second.max_labels)
        if upper is not None and upper != first.min_labels:
            return None  # 有限多值层级区间无法用单个原生模式表达
        return DomainPattern(first.min_labels, upper, self.literals)

    # ---- 输出 ----

    @property
    def fixed_length(self) -> int:
        """原生写法中显式写出的标签数（最左 literal 及其右侧；全 ANY 时为 1）。"""
        return self.literals[-1][0] + 1 if self.literals else 1

    def to_native(self) -> str:
        """恢复为 Mihomo 原生文本。全 ANY 模式也输出合法非空写法（如 ``*``、``+.*``）。"""
        lits = dict(self.literals)
        fixed_len = self.fixed_length
        fixed = ".".join(lits.get(pos, "*") for pos in reversed(range(fixed_len)))
        extra = self.min_labels - fixed_len
        if self.max_labels is None:
            if extra == 0:
                return "+." + fixed
            return "." + "*." * (extra - 1) + fixed
        if self.max_labels != self.min_labels:
            raise ValueError("有限多值层级区间无法表示为单个原生模式")
        return "*." * extra + fixed

    def sort_key(self) -> tuple[tuple[str, ...], int, int]:
        """可读输出的稳定排序键：反向标签序列（ANY 记为 '*'）、长度下界、长度上界。"""
        lits = dict(self.literals)
        labels = tuple(lits.get(pos, "*") for pos in range(self.fixed_length))
        upper = self.max_labels if self.max_labels is not None else _UNBOUNDED_SORT
        return (labels, self.min_labels, upper)

    def __str__(self) -> str:
        return self.to_native()


def _literals_of(labels: list[str]) -> tuple[tuple[int, str], ...]:
    return tuple((pos, label) for pos, label in enumerate(reversed(labels)))
