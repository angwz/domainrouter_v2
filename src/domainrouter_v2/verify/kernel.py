"""内核层验证：用固定版本 Mihomo 的真实解析与求值对照未优化与优化后的产物（规范 §13.1 第 3 层）。

步骤：
1. 按用户 subconverter fork（a33d49e）的规则模拟最终订阅中的 rules 与 rule-providers：
   provider 名取 URL 文件名去扩展名、重名追加 ``_2``；ipcidr 引用追加 ``,no-resolve``；
   内联规则 ``X`` 变为 ``X,组``，三个及以上逗号时按 fork 的正则 ``^(.*?,.*?)(,.*)(,.*)$`` 重排。
2. 生成两套 provider 文件：优化后（实际产物）与未优化（每组原始成员）。规则表完全相同。
3. 由 Go 薄适配器（tools/kernel-adapter）调用 Mihomo 的 ``config.Parse``、provider 加载与
   ``Rule.Match``，对同一批请求给出首个命中的规则序号、目标与是否请求了 DNS 解析。
4. 两套结果逐条必须一致；provider 的加载条目数必须等于文件条目数（防止内核静默跳过条目）。
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from domainrouter_v2.build import BuildResult
from domainrouter_v2.config import Config
from domainrouter_v2.emit import provider_yaml, read_payload
from domainrouter_v2.model.domain import DomainPattern
from domainrouter_v2.model.ip import Network
from domainrouter_v2.model.rule import Member
from domainrouter_v2.planner import CLASSICAL, DOMAIN, IPCIDR, PARTITIONS, Partition, Plan
from domainrouter_v2.tools import ToolError, find_executable, load_specs, tool_dir
from domainrouter_v2.verify.semantic import domain_probes, ip_probes

ADAPTER_SOURCE = Path(__file__).resolve().parents[3] / "tools" / "kernel-adapter"
_FORK_REORDER = re.compile(r"^(.*?,.*?)(,.*)(,.*)$")
_BEHAVIOR = {
    DOMAIN.toml_type: "domain",
    IPCIDR.toml_type: "ipcidr",
    CLASSICAL.toml_type: "classical",
}
MAX_DOMAIN_QUERIES = 40000
MAX_IP_QUERIES = 10000


@dataclass(slots=True)
class KernelResult:
    queries: int = 0
    providers: int = 0
    mismatches: list[str] = field(default_factory=list)
    count_mismatches: list[str] = field(default_factory=list)
    resolve_rules: dict[str, int] = field(default_factory=dict)
    # 每个变体（raw / optimized）的 provider 加载总耗时与单次匹配耗时分布（纳秒）
    load_ns: dict[str, int] = field(default_factory=dict)
    match_ns: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.mismatches and not self.count_mismatches


def find_file_name(url: str) -> str:
    """subconverter ``findFileName``：最后一个 '/' 与最后一个 '.' 之间的文本。"""
    start = url.rfind("/") + 1
    end = url.rfind(".")
    return url[start:end] if end > start else url[start:]


def emulate_subscription(plan: Plan) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """返回 (rules, {provider 名: (behavior, 产物相对路径)})，与 fork 的生成逻辑一致。"""
    rules: list[str] = []
    providers: dict[str, tuple[str, str]] = {}
    for entry in plan.rulesets:
        if entry.type:
            base = find_file_name(entry.ruleset)
            name, suffix = base, 2
            while name in providers:
                name, suffix = f"{base}_{suffix}", suffix + 1
            providers[name] = (_BEHAVIOR[entry.type], _relative_path(entry.ruleset))
            rule = f"RULE-SET,{name},{entry.group}"
            if entry.type == IPCIDR.toml_type:
                rule += ",no-resolve"
            rules.append(rule)
        else:
            text = entry.ruleset.removeprefix("[]")
            if text.startswith("FINAL"):
                text = "MATCH" + text[len("FINAL") :]
            rule = f"{text},{entry.group}"
            if rule.count(",") >= 3:
                rule = _FORK_REORDER.sub(r"\1\3\2", rule)
            rules.append(rule)
    return rules, providers


def _relative_path(url: str) -> str:
    for partition in PARTITIONS:
        marker = f"/{partition.directory}/"
        if marker in url:
            return partition.directory + "/" + url.rsplit(marker, 1)[1]
    raise ValueError(f"无法从 URL 推断产物路径：{url}")


def _provider_entry(behavior: str, path: str, *, mrs: bool) -> dict[str, str]:
    """MRS 变体：domain/ipcidr provider 改读同名 .mrs 文件（classical 没有 MRS）。"""
    if mrs and behavior != "classical":
        return {
            "type": "file",
            "behavior": behavior,
            "format": "mrs",
            "path": "./" + path.removesuffix(".yaml") + ".mrs",
        }
    return {"type": "file", "behavior": behavior, "format": "yaml", "path": f"./{path}"}


def _config_yaml(
    rules: list[str],
    providers: dict[str, tuple[str, str]],
    groups: set[str],
    *,
    mrs: bool = False,
) -> str:
    unreachable = "http://127.0.0.1:9/unreachable"
    config: dict[str, Any] = {
        "mode": "rule",
        "log-level": "silent",
        "geodata-mode": False,
        "geo-auto-update": False,
        "geox-url": {
            "geoip": unreachable,
            "geosite": unreachable,
            "mmdb": unreachable,
            "asn": unreachable,
        },
        "proxies": [],
        "proxy-groups": [
            {"name": name, "type": "select", "proxies": ["DIRECT"]}
            for name in sorted(groups - {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE"})
        ],
        "rule-providers": {
            name: _provider_entry(behavior, path, mrs=mrs)
            for name, (behavior, path) in providers.items()
        },
        "rules": rules,
    }
    return yaml.safe_dump(config, allow_unicode=True, sort_keys=False)


def _queries(result: BuildResult) -> list[dict[str, Any]]:
    assert result.plan is not None
    domains: list[DomainPattern] = []
    networks: list[Network] = []
    ports: set[int] = {443}
    for names, artifact in result.plan.artifacts.items():
        raw = [m for n in names for m in result.collection_members.get(n, [])]
        domains += [m for m in raw if isinstance(m, DomainPattern)] + artifact.domains
        networks += [m for m in raw if isinstance(m, Network)] + artifact.networks
        for condition in artifact.conditions:
            text = condition.render()
            if text.startswith("DST-PORT,"):
                ports.update(int(p.split("-")[0]) for p in text.split(",", 1)[1].split("/"))
    hosts = _sample(sorted(domain_probes(domains)), MAX_DOMAIN_QUERIES)
    addresses = _sample(sorted(ip_probes(networks)), MAX_IP_QUERIES)
    queries: list[dict[str, Any]] = [
        {"id": f"h:{host}", "host": host, "port": 443, "network": "tcp"} for host in hosts
    ]
    ips = [str(_ip(version, value)) for version, value in addresses]
    queries += [{"id": f"i:{ip}", "ip": ip, "port": 443, "network": "tcp"} for ip in ips]
    queries += [
        {"id": f"p:{port}/{net}", "host": "probe.invalid", "port": port, "network": net}
        for port in sorted(ports)
        for net in ("tcp", "udp")
    ]
    return queries


def _sample[T](items: list[T], limit: int) -> list[T]:
    if len(items) <= limit:
        return items
    step = len(items) / limit
    return [items[int(i * step)] for i in range(limit)]


def _ip(version: int, value: int) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    return ipaddress.IPv4Address(value) if version == 4 else ipaddress.IPv6Address(value)


def adapter_binary(config: Config) -> Path:
    """按适配器源码摘要缓存编译结果；源码变化时用已准备的固定 Go 重新编译。"""
    if not ADAPTER_SOURCE.is_dir():
        raise ToolError("找不到 tools/kernel-adapter 源码（内核层验证需要源码检出）")
    digest = hashlib.sha256()
    for name in ("go.mod", "go.sum", "main.go"):
        digest.update((ADAPTER_SOURCE / name).read_bytes())
    suffix = ".exe" if sys.platform == "win32" else ""
    binary = config.state / "tools" / f"kernel-adapter-{digest.hexdigest()[:12]}{suffix}"
    if binary.exists():
        return binary
    specs = load_specs()
    go_root = tool_dir(config.state, specs["go"]) / "go"
    go = find_executable(config.state, specs["go"], [f"go/bin/go{suffix}"])
    env = {
        **os.environ,
        "GOROOT": str(go_root),
        "GOPATH": str(config.state / "gopath"),
        "GOMODCACHE": str(config.state / "gopath" / "pkg" / "mod"),
        "GOCACHE": str(config.state / "gocache"),
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=readonly",
        "CGO_ENABLED": "0",
    }
    subprocess.run(
        [str(go), "build", "-trimpath", "-o", str(binary), "."],
        cwd=ADAPTER_SOURCE,
        env=env,
        check=True,
    )
    return binary


def run_kernel(config: Config, result: BuildResult) -> KernelResult:
    assert result.plan is not None
    specs = load_specs()
    adapter = adapter_binary(config)
    rules, providers = emulate_subscription(result.plan)
    groups = {e.group for e in result.plan.rulesets}
    queries = _queries(result)
    outcome = KernelResult(queries=len(queries), providers=len(providers))
    with tempfile.TemporaryDirectory(prefix="dr2-kernel-") as tmp:
        root = Path(tmp)
        query_file = root / "queries.jsonl"
        query_file.write_text("\n".join(json.dumps(q) for q in queries) + "\n", encoding="utf-8")
        runs: dict[str, dict[str, dict[str, Any]]] = {}
        expected_counts: dict[str, int] = {}
        has_mrs = any(path.endswith(".mrs") for path in result.files)
        variants = ("optimized", "raw", "mrs") if has_mrs else ("optimized", "raw")
        for variant in variants:
            home = root / variant
            home.mkdir()
            for name, filename in (
                ("geoip", "geoip.metadb"),
                ("geosite", "GeoSite.dat"),
                ("asn", "ASN.mmdb"),
            ):
                shutil.copyfile(
                    find_executable(config.state, specs[name], [filename]), home / filename
                )
            files = _variant_files(result, variant)
            for path, data in files.items():
                (home / path).parent.mkdir(parents=True, exist_ok=True)
                (home / path).write_bytes(data)
            (home / "config.yaml").write_text(
                _config_yaml(rules, providers, groups, mrs=variant == "mrs"), encoding="utf-8"
            )
            completed = subprocess.run(
                [str(adapter), str(home), str(home / "config.yaml"), str(query_file)],
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise ToolError(f"内核适配器失败：{completed.stderr.decode('utf-8', 'replace')}")
            lines = [json.loads(line) for line in completed.stdout.decode("utf-8").splitlines()]
            runs[variant] = {line["id"]: line for line in lines if line["kind"] == "query"}
            outcome.load_ns[variant] = sum(
                line.get("nanos", 0) for line in lines if line["kind"] == "provider"
            )
            summary = next(line for line in lines if line["kind"] == "summary")
            outcome.match_ns[variant] = summary.get("nanos", 0) / max(summary["count"], 1)
            if variant in ("optimized", "mrs"):
                # 两个变体都必须加载出与 YAML 条目数相同的规则：MRS 由 YAML 编译而来。
                loaded = {
                    line["provider"]: line["count"] for line in lines if line["kind"] == "provider"
                }
                label = "MRS " if variant == "mrs" else ""
                for name, (_, path) in providers.items():
                    expected_counts[name] = len(read_payload(result.files[path]))
                    if loaded.get(name) != expected_counts[name]:
                        outcome.count_mismatches.append(
                            f"{label}{name}：文件 {expected_counts[name]} 条，"
                            f"Mihomo 加载 {loaded.get(name)} 条"
                        )
        for query in queries:
            a, b = runs["raw"][query["id"]], runs["optimized"][query["id"]]
            if _observation(a) != _observation(b):
                outcome.mismatches.append(
                    f"{query['id']}：未优化 → [{a['index']}] {a.get('rule')}；"
                    f"优化后 → [{b['index']}] {b.get('rule')}"
                )
            if "mrs" in runs:
                c = runs["mrs"][query["id"]]
                if _observation(b) != _observation(c):
                    outcome.mismatches.append(
                        f"{query['id']}：YAML → [{b['index']}] {b.get('rule')}；"
                        f"MRS → [{c['index']}] {c.get('rule')}"
                    )
            if b.get("resolve_requested"):
                key = b.get("resolve_by") or "（未知）"
                outcome.resolve_rules[key] = outcome.resolve_rules.get(key, 0) + 1
    return outcome


def _observation(line: dict[str, Any]) -> tuple[int, str, str]:
    """对照的观察量：首个命中规则的序号、目标策略、请求 DNS 解析的规则。"""
    return (line["index"], line.get("adapter", ""), line.get("resolve_by", ""))


def _variant_files(result: BuildResult, variant: str) -> dict[str, bytes]:
    assert result.plan is not None
    if variant in ("optimized", "mrs"):
        suffixes = (".yaml", ".mrs") if variant == "mrs" else (".yaml",)
        return {p: d for p, d in result.files.items() if p.endswith(suffixes)}
    files: dict[str, bytes] = {}
    for names, artifact in result.plan.artifacts.items():
        raw: list[Member] = [m for n in names for m in result.collection_members.get(n, [])]
        for partition in artifact.partitions():
            members = [m for m in raw if _partition_of(m) is partition]
            files[artifact.path(partition)] = provider_yaml(members)
    return files


def _partition_of(member: Member) -> Partition:
    if isinstance(member, DomainPattern):
        return DOMAIN
    if isinstance(member, Network):
        return IPCIDR
    return CLASSICAL


def run_kernel_verification(config: Config, result: BuildResult) -> int:
    """CLI 入口：打印结果，返回失败组数（0 表示通过）。"""
    try:
        outcome = run_kernel(config, result)
    except (ToolError, subprocess.CalledProcessError) as exc:
        print(f"✗ 内核层验证无法执行：{exc}", file=sys.stderr)
        return 1
    mark = "✓" if outcome.ok else "✗"
    print(
        f"{mark} 内核层（Mihomo v1.19.33）：provider {outcome.providers} 个，"
        f"请求 {outcome.queries} 个，"
        f"不一致 {len(outcome.mismatches)}，条目数不符 {len(outcome.count_mismatches)}"
    )
    for line in (outcome.count_mismatches + outcome.mismatches)[:30]:
        print(f"    {line}", file=sys.stderr)
    for variant, label in (("raw", "未优化"), ("optimized", "优化后"), ("mrs", "MRS")):
        if variant in outcome.match_ns:
            print(
                f"    {label}：provider 加载 {outcome.load_ns[variant] / 1e6:.0f} ms；"
                f"单次完整规则匹配平均 {outcome.match_ns[variant] / 1e3:.2f} µs"
            )
    for rule, count in sorted(outcome.resolve_rules.items(), key=lambda kv: -kv[1]):
        print(f"    触发 DNS 解析：{rule}（{count} 个请求）")
    return 0 if outcome.ok else 1
