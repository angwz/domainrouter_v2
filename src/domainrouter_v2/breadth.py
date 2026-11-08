"""宽泛规则：判定匹配范围过大的规则，过滤上游中的极端条目，并为清单提供分类。

三个等级：
- NARROW：普通规则；
- BROAD：范围大但可能是有意为之（关键词、GEOIP、整个公共后缀、进程……），只提醒；
- EXCESSIVE：几乎等于“全部流量”或公认的通用词（``0.0.0.0/0``、``DOMAIN-KEYWORD,ads``、
  ``NETWORK,UDP``……）。上游规则中的这类条目被过滤；手写规则只提醒、不改写。

判定只看规则本身，不看它属于哪个合集，也不联网。依据与阈值见 docs/rules/broad-rules.md。
本模块不改变保留下来的规则：过滤只缩小来自上游的匹配集合，且每一条都写入清单。
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from functools import cache
from importlib import resources

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import AddressError, Network, parse_network
from domainrouter_v2.model.rule import Condition, Leaf, Logic, Member


class Breadth(IntEnum):
    NARROW = 0
    BROAD = 1
    EXCESSIVE = 2


class Category(StrEnum):
    """清单中的分节，按此顺序输出。"""

    KEYWORD = "DOMAIN-KEYWORD"
    REGEX = "DOMAIN-REGEX"
    PUBLIC_SUFFIX = "整个公共后缀"
    NETWORK = "大网段"
    ASN = "IP-ASN"
    GEO = "GEOIP / GEOSITE"
    PROCESS = "进程与用户"
    CONNECTION = "连接属性"
    LOGIC = "逻辑规则"


@dataclass(frozen=True, slots=True)
class Verdict:
    level: Breadth
    category: Category | None = None
    reason: str = ""


NARROW = Verdict(Breadth.NARROW)

# 关键词长度阈值。AdGuard HostlistCompiler 把短于 5 个字符的非精确模式视为“过短”并丢弃
# （src/transformations/validate.js 的 MAX_PATTERN_LENGTH = 5）。我们更保守：
# ≤ 2 个字符直接过滤（两个字符的子串会命中海量域名），3～4 个字符只提醒。
KEYWORD_DROP_MAX = 2
KEYWORD_WARN_BELOW = 5

# 不限地域、不限用途的通用顶级域（IANA 根区数据库中的 generic 类旧 gTLD）。
# 覆盖其全部域名的规则没有路由意义；ccTLD（如 cn）与品牌 TLD（如 apple）可能是有意为之，只提醒。
GENERIC_TLDS = frozenset({"com", "net", "org", "info", "biz"})

# 网段阈值：RIR 从 IANA 获得的地址块，IPv4 以 /8、IPv6 以 /12 为单位；
# 比它更大的公网网段跨越多个 RIR 分配，不可能对应某个服务。
IPV4_EXCESSIVE_BELOW = 8
IPV6_EXCESSIVE_BELOW = 12
IPV4_BROAD_UPTO = 8
IPV6_BROAD_UPTO = 16

# IANA 特殊用途地址中“非全球可达”的块（iana-ipv4/ipv6-special-registry），以及组播与保留段。
# 完全落在其中的网段只涉及本地/保留地址，不按大网段处理。
_LOCAL_V4 = tuple(
    ipaddress.IPv4Network(text)
    for text in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.0.2.0/24",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "224.0.0.0/3",  # 组播 224/4 与保留 240/4
    )
)
_LOCAL_V6 = tuple(
    ipaddress.IPv6Network(text)
    for text in (
        "::/127",
        "::ffff:0:0/96",
        "100::/64",
        "2001:db8::/32",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
    )
)

# 判断正则/通配是否“匹配一切”的探针：彼此无关的主机名或进程名。全部命中即视为匹配一切。
_HOST_PROBES = (
    "example.com",
    "www.example.org",
    "a.b.c.d.example.net",
    "localhost",
    "xn--fiqs8s.cn",
    "1-2-3.test",
)
_PROCESS_PROBES = ("chrome.exe", "Telegram", "com.android.vending", "sshd")

_CONNECTION_TYPES = frozenset({"DST-PORT", "SRC-PORT", "NETWORK", "DSCP"})
_INBOUND_TYPES = frozenset({"IN-PORT", "IN-TYPE", "IN-USER", "IN-NAME"})
_SOURCE_TYPES = frozenset({"SRC-IP-CIDR", "SRC-IP-SUFFIX", "SRC-IP-ASN", "SRC-GEOIP"})
_WEB_PORTS = (80, 443)


def _data(name: str) -> str:
    return (resources.files("domainrouter_v2") / "data" / name).read_text(encoding="utf-8")


def _entries(text: str) -> list[str]:
    return [s for line in text.splitlines() if (s := line.strip()) and not s.startswith("#")]


@dataclass(frozen=True, slots=True)
class PublicSuffixes:
    """Public Suffix List 的 ICANN 段，按 PSL 算法判断一个名字本身是否为公共后缀。"""

    rules: frozenset[str]
    wildcard_parents: frozenset[str]  # "*.ck" 记为 "ck"
    exceptions: frozenset[str]  # "!www.ck" 记为 "www.ck"
    max_labels: int  # 公共后缀的最大标签数，超过它的名字不必查表；通配规则比父名多一个标签

    @classmethod
    def parse(cls, text: str) -> PublicSuffixes:
        rules: set[str] = set()
        wildcards: set[str] = set()
        exceptions: set[str] = set()
        for entry in _entries(text):
            if entry.startswith("!"):
                exceptions.add(entry[1:])
            elif entry.startswith("*."):
                wildcards.add(entry[2:])
            else:
                rules.add(entry)
        longest = max(e.count(".") + 1 for e in rules | wildcards | exceptions)
        return cls(frozenset(rules), frozenset(wildcards), frozenset(exceptions), longest + 1)

    def is_public_suffix(self, name: str) -> bool:
        if name in self.exceptions:
            return False
        if "." not in name or name in self.rules:
            return True  # PSL 默认规则 "*"：任何单标签名都是公共后缀
        return name.split(".", 1)[1] in self.wildcard_parents


@dataclass(frozen=True, slots=True)
class BreadthPolicy:
    keywords: frozenset[str]
    suffixes: PublicSuffixes

    @classmethod
    def load(cls) -> BreadthPolicy:
        """包内数据：src/domainrouter_v2/data/ 下的关键词表与 PSL。"""
        return cls(
            frozenset(word.lower() for word in _entries(_data("broad_keywords.txt"))),
            PublicSuffixes.parse(_data("public_suffix_icann.txt")),
        )

    # ---- 入口 ----

    def classify(self, member: Member) -> Verdict:
        if isinstance(member, DomainPattern):
            return self._domain_pattern(member)
        if isinstance(member, Network):
            return _network(member, "")
        return self._condition(member)

    # ---- 域名 ----

    def _domain_pattern(self, pattern: DomainPattern) -> Verdict:
        if pattern.max_labels == pattern.min_labels == len(pattern.literals):
            return NARROW  # 精确主机名
        if not pattern.literals:
            if pattern.max_labels == 1:
                return Verdict(Breadth.BROAD, Category.PUBLIC_SUFFIX, "所有单标签主机名")
            return Verdict(Breadth.EXCESSIVE, Category.PUBLIC_SUFFIX, "没有任何固定标签")
        # 从右起连续的固定标签构成锚点；锚点左侧若还有固定标签，范围已被它限定。
        anchor: list[str] = []
        for expected, (pos, label) in enumerate(pattern.literals):
            if pos != expected:
                return NARROW
            anchor.append(label)
        return self._suffix(".".join(reversed(anchor)))

    def _suffix(self, name: str) -> Verdict:
        if name.count(".") + 1 > self.suffixes.max_labels:
            return NARROW
        if not self.suffixes.is_public_suffix(name):
            return NARROW
        if name in GENERIC_TLDS:
            return Verdict(
                Breadth.EXCESSIVE, Category.PUBLIC_SUFFIX, f"覆盖通用顶级域 .{name} 下的全部域名"
            )
        return Verdict(Breadth.BROAD, Category.PUBLIC_SUFFIX, f"覆盖公共后缀 .{name} 下的域名")

    def _keyword(self, keyword: str) -> Verdict:
        word = keyword.lower().strip(".-")
        if len(word) <= KEYWORD_DROP_MAX:
            return Verdict(Breadth.EXCESSIVE, Category.KEYWORD, f"关键词只有 {len(word)} 个字符")
        if word in self.keywords:
            return Verdict(Breadth.EXCESSIVE, Category.KEYWORD, f"通用词「{word}」在宽泛关键词表中")
        if len(word) < KEYWORD_WARN_BELOW:
            return Verdict(Breadth.BROAD, Category.KEYWORD, f"短关键词（{len(word)} 个字符）")
        return Verdict(Breadth.BROAD, Category.KEYWORD, "子串匹配")

    def _wildcard(self, payload: str) -> Verdict:
        """DOMAIN-WILDCARD：最后一个通配符之后的完整标签构成锚点。"""
        tail = re.split(r"[*?]", payload)[-1]
        if tail == payload:
            return NARROW  # 没有通配符
        anchor = tail[1:] if tail.startswith(".") else tail.partition(".")[2]
        if not anchor:
            return Verdict(Breadth.EXCESSIVE, Category.PUBLIC_SUFFIX, "通配之后没有完整标签")
        return self._suffix(anchor.lower())

    # ---- 条件 ----

    def _condition(self, condition: Condition) -> Verdict:
        if isinstance(condition, Logic):
            return self._logic(condition)
        return self._leaf(condition)

    def _logic(self, logic: Logic) -> Verdict:
        children = [self._condition(child) for child in logic.children]
        if logic.op == "NOT":
            if children[0].level is Breadth.NARROW:
                return Verdict(Breadth.EXCESSIVE, Category.LOGIC, "NOT 取反后匹配几乎全部流量")
            return Verdict(Breadth.BROAD, Category.LOGIC, "NOT 取反")
        # AND 的范围由最窄的子条件决定，OR 由最宽的决定。
        pick = min if logic.op == "AND" else max
        level = pick(child.level for child in children)
        if level is Breadth.NARROW:
            return NARROW
        reasons = "；".join(c.reason for c in children if c.level is level)
        return Verdict(level, Category.LOGIC, f"{logic.op}：{reasons}")

    def _leaf(self, leaf: Leaf) -> Verdict:
        kind, payload = leaf.type, leaf.payload
        if kind == "DOMAIN-KEYWORD":
            return self._keyword(payload)
        if kind == "DOMAIN-REGEX":
            return _regex(payload, _HOST_PROBES, Category.REGEX, "正则")
        if kind == "DOMAIN-WILDCARD":
            return self._wildcard(payload)
        if kind == "DOMAIN-SUFFIX":
            return self._suffix(payload.lower().lstrip("."))
        if kind in {"IP-CIDR", "IP-CIDR6"}:
            return _cidr(payload, "")
        if kind == "IP-ASN":
            return Verdict(Breadth.BROAD, Category.ASN, "整个自治系统的地址")
        if kind in {"GEOIP", "GEOSITE"}:
            return Verdict(Breadth.BROAD, Category.GEO, "整个国家/地区或站点分类")
        if kind == "IP-SUFFIX":
            return _ip_suffix(payload)
        if kind.startswith("PROCESS-") or kind == "UID":
            return _process(kind, payload)
        if kind in _INBOUND_TYPES:
            return Verdict(Breadth.EXCESSIVE, Category.CONNECTION, "命中该入站的全部流量")
        if kind == "NETWORK":
            return Verdict(Breadth.EXCESSIVE, Category.CONNECTION, f"全部 {payload.upper()} 流量")
        if kind == "DST-PORT" and _covers_web_port(payload):
            return Verdict(
                Breadth.EXCESSIVE, Category.CONNECTION, "目标端口包含 80/443，即全部网页流量"
            )
        if kind == "SRC-IP-CIDR":
            return _cidr(payload, "来源 ")
        if kind in _CONNECTION_TYPES or kind in _SOURCE_TYPES:
            return Verdict(Breadth.BROAD, Category.CONNECTION, "不区分目标，按连接属性匹配")
        return NARROW


def _network(network: Network, role: str) -> Verdict:
    v4 = network.version == 4
    excessive_below = IPV4_EXCESSIVE_BELOW if v4 else IPV6_EXCESSIVE_BELOW
    broad_upto = IPV4_BROAD_UPTO if v4 else IPV6_BROAD_UPTO
    if network.prefix > broad_upto:
        return NARROW  # 快速路径：绝大多数网段在这里返回
    if v4:
        net4 = ipaddress.IPv4Network((network.address, network.prefix))
        local = any(net4.subnet_of(block) for block in _LOCAL_V4)
    else:
        net6 = ipaddress.IPv6Network((network.address, network.prefix))
        local = any(net6.subnet_of(block) for block in _LOCAL_V6)
    if local:
        return NARROW
    if network.prefix < excessive_below:
        size = "全部地址" if network.prefix == 0 else f"/{network.prefix} 跨越多个 RIR 地址块"
        return Verdict(Breadth.EXCESSIVE, Category.NETWORK, f"{role}{size}")
    return Verdict(Breadth.BROAD, Category.NETWORK, f"{role}/{network.prefix} 大网段")


def _cidr(payload: str, role: str) -> Verdict:
    try:
        return _network(parse_network(payload).network, role)
    except AddressError:
        return NARROW


def _ip_suffix(payload: str) -> Verdict:
    _, _, bits = payload.partition("/")
    if bits.isdigit() and int(bits) == 0:
        return Verdict(Breadth.EXCESSIVE, Category.NETWORK, "IP-SUFFIX /0 匹配全部地址")
    return Verdict(Breadth.BROAD, Category.NETWORK, "按地址低位匹配，跨越所有网段")


def _process(kind: str, payload: str) -> Verdict:
    if kind.endswith("-WILDCARD") and not payload.strip("*?"):
        return Verdict(Breadth.EXCESSIVE, Category.PROCESS, "通配匹配所有进程")
    if kind.endswith("-REGEX"):
        verdict = _regex(payload, _PROCESS_PROBES, Category.PROCESS, "进程正则")
        if verdict.level is Breadth.EXCESSIVE:
            return verdict
    who = "该用户" if kind == "UID" else "该程序"
    return Verdict(Breadth.BROAD, Category.PROCESS, f"{who}的全部流量")


@cache
def _regex(pattern: str, probes: tuple[str, ...], category: Category, label: str) -> Verdict:
    """Mihomo 用 Go regexp 的 MatchString（不锚定）；这里用 Python re 近似判断是否匹配一切。"""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return Verdict(Breadth.BROAD, category, f"{label}（无法用 Python 判断范围）")
    if all(compiled.search(probe) for probe in probes):
        return Verdict(Breadth.EXCESSIVE, category, f"{label}匹配任意名称")
    return Verdict(Breadth.BROAD, category, label)


def _covers_web_port(spec: str) -> bool:
    for part in spec.split("/"):
        low, _, high = part.partition("-")
        if not low.isdigit():
            continue
        lo, hi = int(low), int(high) if high.isdigit() else int(low)
        if any(lo <= port <= hi for port in _WEB_PORTS):
            return True
    return False


# ---- 过滤结果与清单 ----


@dataclass(frozen=True, slots=True)
class FilteredRule:
    """被过滤的上游规则。"""

    text: str
    verdict: Verdict
    collection: str
    source: str  # 来源 URL


@dataclass(frozen=True, slots=True)
class ListedRule:
    """已写入规则文件、但范围较大的规则。"""

    text: str
    verdict: Verdict
    handwritten: bool


@dataclass(frozen=True, slots=True)
class FileListing:
    path: str
    targets: tuple[str, ...]
    rules: tuple[ListedRule, ...]


def render_listing(filtered: list[FilteredRule], files: list[FileListing]) -> bytes:
    """reports/broad-rules.md：确定性内容（无时间），随规则文件一起发布。"""
    lines = [
        "# 宽泛规则清单",
        "",
        "列出两类规则，判定依据见项目文档 docs/rules/broad-rules.md：",
        "",
        "- **已过滤**：上游规则中范围接近全部流量或使用通用词关键词的条目，未写入规则文件；",
        "- **已发布**：仍在规则文件中、但范围较大的规则，按类别和文件列出，供你检查。",
        "",
        "手写在 my.wei 中的规则不会被过滤，单独标为「手写」。",
        "",
        f"## 已过滤（{len(filtered)}）",
        "",
    ]
    if filtered:
        lines += ["| 规则 | 原因 | 合集 | 来源 |", "| --- | --- | --- | --- |"]
        lines += [
            f"| `{_cell(f.text)}` | {f.verdict.reason} | {f.collection} | {f.source} |"
            for f in sorted(filtered, key=lambda f: (f.collection, f.text, f.source))
        ]
    else:
        lines.append("没有。")
    for category in Category:
        sections: list[tuple[FileListing, list[ListedRule]]] = []
        for listing in files:
            rules = [r for r in listing.rules if r.verdict.category is category]
            if rules:
                sections.append((listing, rules))
        total = sum(len(rules) for _, rules in sections)
        if not total:
            continue
        lines += ["", f"## 已发布：{category.value}（{total}）", ""]
        for listing, rules in sections:
            lines += [f"`{listing.path}` → {'、'.join(listing.targets)}", ""]
            # 同一说明的规则合成一行，避免几百行重复的“子串匹配”。
            grouped: dict[str, list[str]] = {}
            for rule in rules:
                note = ("手写 · " if rule.handwritten else "") + rule.verdict.reason
                # 分节标题已是类型名时只显示载荷，例如 DOMAIN-KEYWORD 节里写 `google`。
                shown = rule.text.removeprefix(f"{category.value},")
                grouped.setdefault(note, []).append(f"`{_cell(shown)}`")
            lines += [f"- {note}：{' '.join(items)}" for note, items in grouped.items()]
            lines.append("")
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")


def _cell(text: str) -> str:
    """表格与行内代码中不能出现的字符：竖线转义，反引号改为单引号。"""
    return text.replace("|", r"\|").replace("`", "'")
