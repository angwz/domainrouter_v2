"""网段解析与精确合并（merge-cases §6，规范 I01–I09）。"""

from __future__ import annotations

import ipaddress
import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domainrouter_v2.model.ip import AddressError, Network, merge_networks, parse_network


def nets(*texts: str) -> list[Network]:
    return [parse_network(t).network for t in texts]


def strs(networks: list[Network]) -> list[str]:
    return [str(n) for n in networks]


@pytest.mark.parametrize(
    ("text", "expected", "cleared", "unmapped"),
    [
        ("1.2.3.4", "1.2.3.4/32", False, False),
        ("2001:db8::1", "2001:db8::1/128", False, False),
        ("1.2.3.5/24", "1.2.3.0/24", True, False),
        ("1.2.3.0/24", "1.2.3.0/24", False, False),
        ("::ffff:1.2.3.4", "1.2.3.4/32", False, True),
        ("::ffff:1.2.3.0/120", "1.2.3.0/24", False, True),
        ("::fffe:0:0/95", "::fffe:0:0/95", False, False),
    ],
)
def test_parse(text: str, expected: str, cleared: bool, unmapped: bool) -> None:
    parsed = parse_network(text)
    assert str(parsed.network) == expected
    assert parsed.host_bits_cleared is cleared
    assert parsed.unmapped is unmapped


@pytest.mark.parametrize("text", ["1.2.3.0/33", "fe80::1%eth0", "a.com", "1.2.3"])
def test_parse_rejects(text: str) -> None:
    with pytest.raises(AddressError):
        parse_network(text)


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        (("10.0.0.0/8", "10.1.0.0/16", "10.1.2.3"), ["10.0.0.0/8"]),
        (("192.0.2.0/25", "192.0.2.128/25"), ["192.0.2.0/24"]),
        (("192.0.2.0/26", "192.0.2.128/26"), ["192.0.2.0/26", "192.0.2.128/26"]),
        (("192.0.2.1", "192.0.2.3"), ["192.0.2.1/32", "192.0.2.3/32"]),
        (("192.0.2.0/25", "192.0.2.128/26"), ["192.0.2.0/25", "192.0.2.128/26"]),
        (("0.0.0.0/0", "1.2.3.4"), ["0.0.0.0/0"]),
        (("255.255.255.255", "255.255.255.254"), ["255.255.255.254/31"]),
        (("::/0", "2001:db8::/32"), ["::/0"]),
        (("10.0.0.0/8", "2001:db8::/32"), ["10.0.0.0/8", "2001:db8::/32"]),
    ],
)
def test_merge(inputs: tuple[str, ...], expected: list[str]) -> None:
    assert strs(merge_networks(nets(*inputs))) == expected


@st.composite
def small_v4(draw: st.DrawFn) -> Network:
    # 集中在 10.0.0.0/24 附近，制造大量重叠、相邻与空洞
    prefix = draw(st.integers(min_value=26, max_value=32))
    host = draw(st.integers(min_value=0, max_value=255))
    return parse_network(f"10.0.0.{host}/{prefix}").network


@settings(max_examples=1000)
@given(st.lists(small_v4(), max_size=12))
def test_merge_preserves_address_set(networks: list[Network]) -> None:
    def addresses(items: list[Network]) -> set[int]:
        return {a for n in items for a in range(n.first, n.last + 1)}

    merged = merge_networks(networks)
    assert addresses(merged) == addresses(networks)
    # 结果互不重叠且已排序
    for left, right in itertools.pairwise(merged):
        assert left.last < right.first
    # 与标准库交叉校验（不作为唯一依据）
    std = ipaddress.collapse_addresses(ipaddress.ip_network(str(n)) for n in networks)
    assert strs(merged) == [str(n) for n in std]
