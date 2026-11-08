"""规则类型注册表：精确识别类型名，登记其分区、成本次序与目标 IP 属性。

所有来源格式先把各自的类型名映射到这里的 Mihomo 规范名，再统一处理；
禁止用 ``startswith("DOMAIN")`` 之类的前缀判断类型（规范 §5）。
依据：https://wiki.metacubex.one/en/config/rules/ （mihomo v1.19.33）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    DOMAIN = "domain"  # DOMAIN / DOMAIN-SUFFIX：进入 domain 集合
    DST_CIDR = "dst-cidr"  # 目标 IP-CIDR：进入 ipcidr 集合
    CLASSICAL = "classical"  # 逐条求值的条件
    LOGIC = "logic"  # AND / OR / NOT
    CONTROL = "control"  # MATCH / RULE-SET / SUB-RULE：不能作为合集成员


@dataclass(frozen=True, slots=True)
class RuleType:
    name: str
    kind: Kind
    rank: int = 0  # classical 内的成本次序（merge-cases §1），越小越先判断
    target_ip: bool = False  # 目标 IP 条件：可能触发 DNS，需要 no-resolve
    src_variant: str | None = None  # 带 src 参数时等价的来源类型


_RANK_METADATA = 1
_RANK_SOURCE = 2
_RANK_KEYWORD = 3
_RANK_WILDCARD = 4
_RANK_GEOSITE = 5
_RANK_REGEX = 6
_RANK_TARGET_IP = 7
_RANK_LOGIC = 8
_RANK_PROCESS = 9

_TYPES = [
    RuleType("DOMAIN", Kind.DOMAIN),
    RuleType("DOMAIN-SUFFIX", Kind.DOMAIN),
    RuleType("DOMAIN-KEYWORD", Kind.CLASSICAL, _RANK_KEYWORD),
    RuleType("DOMAIN-WILDCARD", Kind.CLASSICAL, _RANK_WILDCARD),
    RuleType("DOMAIN-REGEX", Kind.CLASSICAL, _RANK_REGEX),
    RuleType("GEOSITE", Kind.CLASSICAL, _RANK_GEOSITE),
    RuleType("IP-CIDR", Kind.DST_CIDR, target_ip=True, src_variant="SRC-IP-CIDR"),
    RuleType("IP-CIDR6", Kind.DST_CIDR, target_ip=True, src_variant="SRC-IP-CIDR"),
    RuleType("IP-SUFFIX", Kind.CLASSICAL, _RANK_TARGET_IP, True, "SRC-IP-SUFFIX"),
    RuleType("IP-ASN", Kind.CLASSICAL, _RANK_TARGET_IP, True, "SRC-IP-ASN"),
    RuleType("GEOIP", Kind.CLASSICAL, _RANK_TARGET_IP, True, "SRC-GEOIP"),
    RuleType("SRC-GEOIP", Kind.CLASSICAL, _RANK_SOURCE),
    RuleType("SRC-IP-ASN", Kind.CLASSICAL, _RANK_SOURCE),
    RuleType("SRC-IP-CIDR", Kind.CLASSICAL, _RANK_SOURCE),
    RuleType("SRC-IP-SUFFIX", Kind.CLASSICAL, _RANK_SOURCE),
    RuleType("DST-PORT", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("SRC-PORT", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("IN-PORT", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("IN-TYPE", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("IN-USER", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("IN-NAME", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("NETWORK", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("DSCP", Kind.CLASSICAL, _RANK_METADATA),
    RuleType("PROCESS-NAME", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("PROCESS-NAME-WILDCARD", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("PROCESS-NAME-REGEX", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("PROCESS-PATH", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("PROCESS-PATH-WILDCARD", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("PROCESS-PATH-REGEX", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("UID", Kind.CLASSICAL, _RANK_PROCESS),
    RuleType("AND", Kind.LOGIC, _RANK_LOGIC),
    RuleType("OR", Kind.LOGIC, _RANK_LOGIC),
    RuleType("NOT", Kind.LOGIC, _RANK_LOGIC),
    RuleType("MATCH", Kind.CONTROL),
    RuleType("RULE-SET", Kind.CONTROL),
    RuleType("SUB-RULE", Kind.CONTROL),
]

TYPES: dict[str, RuleType] = {t.name: t for t in _TYPES}

# 其他客户端的同义类型名 → Mihomo 规范名（各自官方文档）。
ALIASES: dict[str, str] = {
    "FINAL": "MATCH",  # Surge / Loon / 旧 Clash
    "DEST-PORT": "DST-PORT",  # Surge / Loon
    "SRC-IP": "SRC-IP-CIDR",  # Surge
}

# 有官方定义、但 Mihomo 无等价条件的类型 → 跳过原因。
UNSUPPORTED: dict[str, str] = {
    "USER-AGENT": "需要 MITM 解密 HTTPS 才能匹配，Mihomo 不支持",
    "URL-REGEX": "需要 MITM 解密 HTTPS 才能匹配，Mihomo 不支持",
    "SUBNET": "Mihomo 没有按所连网络匹配的条件",
    "CELLULAR-RADIO": "Mihomo 没有蜂窝网络条件",
    "CELLULAR-CARRIER": "Mihomo 没有蜂窝网络条件",
    "DEVICE-NAME": "Mihomo 没有设备名条件",
    "MAC-ADDRESS": "Mihomo 没有 MAC 地址条件",
    "SCRIPT": "脚本规则无法转换",
    "HOSTNAME-TYPE": "Mihomo 没有主机名类型条件",
    "DOMAIN-SET": "嵌套引用不自动展开，请在 my.wei 中直接引用该来源",
}

KNOWN_PARAMS = frozenset(
    {
        "no-resolve",
        "src",
        "extended-matching",  # Surge
        "pre-matching",  # Surge
        "force-remote-dns",  # Loon
    }
)
# 带值的参数（如 notification-text=…）按前缀识别。
KNOWN_PARAM_PREFIXES = ("notification-text=", "notification-interval=", "update-interval=")


def canonical_type(token: str) -> str:
    """类型名按 ASCII 大写，再解析同义名。"""
    upper = token.strip().upper()
    return ALIASES.get(upper, upper)


def is_known_param(field: str) -> bool:
    lowered = field.strip().lower()
    return lowered in KNOWN_PARAMS or lowered.startswith(KNOWN_PARAM_PREFIXES)
