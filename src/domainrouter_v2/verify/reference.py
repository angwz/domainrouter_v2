"""独立参考解释器：直接按原生文本逐标签匹配，用来交叉检查优化器。

刻意不复用 ``DomainPattern``、trie 或包含判定：参考实现必须从另一条路径得出结论，
否则优化器的错误会被同样的代码「证明」为正确（规范 1.5 §13.1 第 2 层）。
"""

from __future__ import annotations

import ipaddress


def native_domain_match(pattern: str, host: str) -> bool:
    """判断已规范化的主机名是否命中 Mihomo 原生域名模式文本。

    规则：``+.`` 前缀允许 0 个或更多额外标签，``.`` 前缀要求至少 1 个；
    ``*`` 标签匹配恰好一个非空标签；其余标签逐字比较。
    """
    min_extra, unbounded = 0, False
    body = pattern
    if body.startswith("+."):
        body, unbounded = body[2:], True
    elif body.startswith("."):
        body, min_extra, unbounded = body[1:], 1, True
    want = body.split(".")
    got = host.split(".")
    if any(label == "" for label in got):
        return False
    extra = len(got) - len(want)
    if extra < min_extra or (not unbounded and extra != 0):
        return False
    tail = got[extra:]
    return all(w in ("*", g) for w, g in zip(want, tail, strict=True))


def native_ip_match(cidr: str, address: str) -> bool:
    """判断地址是否落在网段内（地址族不同时不匹配）。"""
    net = ipaddress.ip_network(cidr, strict=True)
    addr = ipaddress.ip_address(address)
    return addr.version == net.version and addr in net
