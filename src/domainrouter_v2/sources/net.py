"""HTTP 传输：带 Happy Eyeballs（RFC 8305）地址竞速的 httpx 传输层。

背景：Python 的 ``socket.create_connection`` 按 getaddrinfo 顺序逐个尝试地址。
在「能解析 AAAA 但 IPv6 不通」的网络里，每个 IPv6 地址都要等到连接超时，
实测下载 210 个来源从约 1 分钟拖到 17 分钟。curl 与浏览器用 Happy Eyeballs 避免这个问题。

做法：先按地址族交替排列解析结果，每隔 250ms 启动一路连接探测，第一路成功即选定该地址；
随后让 httpcore 直连这个 IP（TLS 的 SNI 与证书校验仍使用原主机名）。选定结果按主机缓存，
连接失败时清除缓存并重新竞速。代理（HTTPS_PROXY 等环境变量）仍由 httpx 自行处理。
"""

from __future__ import annotations

import ipaddress
import socket
import threading
from collections.abc import Iterable

import httpcore
import httpx

ATTEMPT_DELAY_SECONDS = 0.25

_cache: dict[tuple[str, int], str] = {}
_cache_lock = threading.Lock()


def interleave(infos: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """RFC 8305 §4：按首选地址族开始，两个地址族交替。"""
    if not infos:
        return []
    first = infos[0][0]
    primary = [i for i in infos if i[0] == first]
    secondary = [i for i in infos if i[0] != first]
    out: list[tuple[int, str]] = []
    for index in range(max(len(primary), len(secondary))):
        out.extend(group[index] for group in (primary, secondary) if index < len(group))
    return out


def race(candidates: Iterable[tuple[int, str]], port: int, timeout: float) -> str:
    """错开启动的并行连接探测，返回第一个连通的地址。全部失败抛 ConnectError。"""
    done = threading.Event()
    winner: list[str] = []
    lock = threading.Lock()
    pending: list[threading.Thread] = []

    def attempt(family: int, address: str) -> None:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((address, port))
        except OSError:
            return
        finally:
            sock.close()
        with lock:
            if not winner:
                winner.append(address)
                done.set()

    for index, (family, address) in enumerate(candidates):
        if index and done.wait(ATTEMPT_DELAY_SECONDS):
            break
        thread = threading.Thread(target=attempt, args=(family, address), daemon=True)
        thread.start()
        pending.append(thread)
    deadline_wait = timeout
    while not done.is_set() and any(t.is_alive() for t in pending) and deadline_wait > 0:
        done.wait(0.05)
        deadline_wait -= 0.05
    if not winner:
        raise httpcore.ConnectError("所有地址都无法连接")
    return winner[0]


def pick_address(host: str, port: int, timeout: float) -> str:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return host
    with _cache_lock:
        cached = _cache.get((host, port))
    if cached is not None:
        return cached
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise httpcore.ConnectError(f"无法解析主机名 {host}：{exc}") from exc
    unique = dict.fromkeys((int(fam), str(addr[0])) for fam, _, _, _, addr in infos)
    candidates = interleave(list(unique))
    address = race(candidates, port, timeout)
    with _cache_lock:
        _cache[(host, port)] = address
    return address


class HappyEyeballsBackend(httpcore.SyncBackend):
    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        limit = timeout if timeout is not None else 10.0
        address = pick_address(host, port, limit)
        try:
            return super().connect_tcp(address, port, timeout, local_address, socket_options)
        except httpcore.ConnectError:
            with _cache_lock:
                _cache.pop((host, port), None)
            raise


def make_transport() -> httpx.HTTPTransport:
    """httpx 默认传输，但连接建立改用 Happy Eyeballs。

    httpx 0.28 没有公开注入 network_backend 的参数，这里替换其内部连接池；
    依赖版本已在 pyproject 中限定为 <0.29，并有测试检查该属性仍然存在。
    """
    transport = httpx.HTTPTransport()
    transport._pool = httpcore.ConnectionPool(
        ssl_context=httpx.create_ssl_context(),
        network_backend=HappyEyeballsBackend(),
    )
    return transport
