"""优化器合成数据基准（规范 §13.4）：不同分布与规模下的耗时、峰值内存与输出规模。

用法：uv run python tools/bench/optimizer_bench.py [规模 …]，默认 10000 100000。
数据由固定种子生成，可重复；只测优化算法本身，不含解析与 I/O。
"""

from __future__ import annotations

import platform
import random
import sys
import time
import tracemalloc
from collections.abc import Callable

from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network, merge_networks, parse_network
from domainrouter_v2.optimize.domain import optimize_domains

SEED = 20261108
LETTERS = "abcdefghijklmnopqrstuvwxyz0123456789"


def label(rng: random.Random, length: int) -> str:
    return "".join(rng.choice(LETTERS) for _ in range(length))


def suffix_heavy(n: int, rng: random.Random) -> list[DomainPattern]:
    """大面积后缀覆盖：少量 +.x 覆盖大量子域。"""
    bases = [f"{label(rng, 6)}.com" for _ in range(max(1, n // 100))]
    out = [DomainPattern.suffix(b) for b in bases]
    while len(out) < n:
        base = rng.choice(bases)
        out.append(DomainPattern.exact(f"{label(rng, 5)}.{label(rng, 4)}.{base}"))
    return out


def disjoint(n: int, rng: random.Random) -> list[DomainPattern]:
    """全部互不包含。"""
    return [DomainPattern.exact(f"{label(rng, 8)}.{label(rng, 6)}.net") for _ in range(n)]


def long_labels(n: int, rng: random.Random) -> list[DomainPattern]:
    return [
        DomainPattern.suffix(".".join(label(rng, 40) for _ in range(4)) + ".org") for _ in range(n)
    ]


def wildcards(n: int, rng: random.Random) -> list[DomainPattern]:
    """多通配：中间 ANY、一级通配与后缀混合。"""
    bases = [f"{label(rng, 5)}.io" for _ in range(max(1, n // 50))]
    out: list[DomainPattern] = []
    while len(out) < n:
        base = rng.choice(bases)
        choices = [
            f"*.{base}",
            f"x.*.{base}",
            f"+.*.{label(rng, 3)}.{base}",
            f"z{label(rng, 4)}.{base}",
        ]
        out.append(DomainPattern.parse_native(rng.choice(choices)))
    return out


def ipv4_mixed(n: int, rng: random.Random) -> list[Network]:
    out: list[Network] = []
    for _ in range(n):
        a, b, c = rng.randrange(1, 224), rng.randrange(256), rng.randrange(256)
        out.append(parse_network(f"{a}.{b}.{c}.0/{rng.choice([16, 20, 24, 28, 32])}").network)
    return out


def ipv6_large(n: int, rng: random.Random) -> list[Network]:
    out: list[Network] = []
    for _ in range(n):
        a, b = rng.randrange(0x10000), rng.randrange(0x10000)
        out.append(parse_network(f"2001:{a:x}:{b:x}::/{rng.choice([32, 40, 48, 56, 64])}").network)
    return out


CASES: dict[str, tuple[Callable[[int, random.Random], list], Callable[[list], object]]] = {  # type: ignore[type-arg]
    "域名·大面积后缀覆盖": (suffix_heavy, optimize_domains),
    "域名·全部互不包含": (disjoint, optimize_domains),
    "域名·长标签": (long_labels, optimize_domains),
    "域名·多通配": (wildcards, optimize_domains),
    "IPv4·混合网段": (ipv4_mixed, merge_networks),
    "IPv6·大范围": (ipv6_large, merge_networks),
}


def output_size(result: object) -> int:
    if isinstance(result, tuple):
        return len(result[0])
    assert isinstance(result, list)
    return len(result)


def main(sizes: list[int]) -> None:
    print(f"Python {platform.python_version()} · {platform.system()} {platform.machine()}")
    print("| 分布 | 输入 | 输出 | 耗时 (s) | 峰值内存 (MiB) |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for name, (generate, optimize) in CASES.items():
        for size in sizes:
            data = generate(size, random.Random(SEED))
            tracemalloc.start()
            started = time.perf_counter()
            result = optimize(data)
            elapsed = time.perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            print(
                f"| {name} | {size} | {output_size(result)} | {elapsed:.2f} | {peak / 2**20:.1f} |"
            )


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [10_000, 100_000])
