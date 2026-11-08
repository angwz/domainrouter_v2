"""IP 网段的解析、规范化与精确集合合并。

网段统一表示为地址族内的整数闭区间，合并算法（规范 1.5 §9.4）：
1. 按 (起点, 终点) 排序；
2. 合并重叠以及首尾相接（无空隙）的区间；
3. 把每段区间分解为精确覆盖它的最少对齐 CIDR。
复杂度 O(n log n)（排序）加 O(输出 × 地址位数)（分解），不枚举地址。
IPv4 与 IPv6 永远分开处理。
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from dataclasses import dataclass

_BITS = {4: 32, 6: 128}
_MAPPED_PREFIX = ipaddress.IPv6Network("::ffff:0:0/96")


class AddressError(ValueError):
    """不是合法的地址或网段。"""


@dataclass(frozen=True, slots=True, order=True)
class Network:
    """一个规范化的 CIDR：主机位已清零。按 (地址族, 网络地址, 前缀长度) 排序。"""

    version: int
    address: int
    prefix: int

    @property
    def first(self) -> int:
        return self.address

    @property
    def last(self) -> int:
        return self.address + (1 << (_BITS[self.version] - self.prefix)) - 1

    def contains(self, other: Network) -> bool:
        return (
            self.version == other.version and self.first <= other.first and other.last <= self.last
        )

    def __str__(self) -> str:
        cls = ipaddress.IPv4Network if self.version == 4 else ipaddress.IPv6Network
        return str(cls((self.address, self.prefix)))


@dataclass(frozen=True, slots=True)
class ParsedNetwork:
    network: Network
    original: str
    host_bits_cleared: bool  # 输入带主机位，已按掩码规范化
    unmapped: bool  # IPv4 映射的 IPv6 已还原为 IPv4


def is_ip_like(text: str) -> bool:
    """快速判断文本是否「看起来」是地址或网段（用于先识别 IP 再识别域名）。"""
    try:
        parse_network(text)
    except AddressError:
        return False
    return True


def parse_network(text: str) -> ParsedNetwork:
    """解析单个地址或 CIDR。单个 IPv4 → /32，IPv6 → /128。

    - 带主机位的 CIDR 按掩码规范化并标记；
    - zone ID（``fe80::1%eth0``）不是目标地址，拒绝；
    - 完全落在 ``::ffff:0:0/96`` 内的映射地址/前缀还原为 IPv4；
      包含整个映射段的更大 IPv6 网段（如 ``::/0``）保持为 IPv6，不做跨地址族折叠。
    """
    raw = text.strip()
    if "%" in raw:
        raise AddressError(f"含 zone ID 的地址不是目标地址：{raw!r}")
    try:
        net = ipaddress.ip_network(raw, strict=False)
    except ValueError as exc:
        raise AddressError(f"不是合法的地址或网段：{raw!r}") from exc
    cleared = "/" in raw and net.network_address != ipaddress.ip_interface(raw).ip
    unmapped = False
    if isinstance(net, ipaddress.IPv6Network) and net.subnet_of(_MAPPED_PREFIX):
        mapped = net.network_address.ipv4_mapped
        assert mapped is not None  # subnet_of 已保证
        net = ipaddress.IPv4Network((int(mapped), net.prefixlen - 96))
        unmapped = True
    return ParsedNetwork(
        Network(net.version, int(net.network_address), net.prefixlen), raw, cleared, unmapped
    )


def merge_networks(networks: Iterable[Network]) -> list[Network]:
    """返回与输入地址集合完全相同的最少对齐 CIDR 列表（按版本、地址排序）。"""
    items = list(networks)
    result: list[Network] = []
    for version in (4, 6):
        ranges = sorted((n.first, n.last) for n in items if n.version == version)
        merged: list[tuple[int, int]] = []
        for first, last in ranges:
            if merged and first <= merged[-1][1] + 1:
                if last > merged[-1][1]:
                    merged[-1] = (merged[-1][0], last)
            else:
                merged.append((first, last))
        for first, last in merged:
            result.extend(_range_to_cidrs(version, first, last))
    return result


def _range_to_cidrs(version: int, first: int, last: int) -> list[Network]:
    """把整数闭区间分解为最少的对齐 CIDR（贪心：每步取起点对齐且不越界的最大块）。"""
    bits = _BITS[version]
    out: list[Network] = []
    while first <= last:
        # 起点的对齐粒度：最低位 1 的位置；first == 0 时可对齐到整个地址空间
        align = (first & -first).bit_length() - 1 if first else bits
        span = (last - first + 1).bit_length() - 1
        size = min(align, span)
        out.append(Network(version, first, bits - size))
        first += 1 << size
    return out
