"""构建编排：读取输入与快照 → 解析 → 规划与优化 → 渲染 → 原子写出。

构建不联网：上游内容只来自 ``fetch`` 写入的快照。任何 error 级诊断都会阻止写出，
已有的输出目录保持不变（规范 §11.1、§15.2）。
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from domainrouter_v2.breadth import (
    Breadth,
    BreadthPolicy,
    FileListing,
    FilteredRule,
    ListedRule,
    Verdict,
    render_listing,
)
from domainrouter_v2.config import Config
from domainrouter_v2.diagnostics import Code, Diagnostic, error, has_errors, warning
from domainrouter_v2.emit import render_outputs, sha256
from domainrouter_v2.groups import is_known_target, validate_groups
from domainrouter_v2.model.profile import LocalMember, Profile, RouteKind, SourceRef
from domainrouter_v2.model.rule import Member, render_member
from domainrouter_v2.parse.document import parse_profile
from domainrouter_v2.planner import PARTITIONS, Plan, build_plan
from domainrouter_v2.sources.snapshot import Snapshot, StateStore, source_id


@dataclass(slots=True)
class SourceState:
    sid: str
    ref: SourceRef
    snapshot: Snapshot | None
    consecutive_failures: int
    first_failure: str
    last_error: str


@dataclass(slots=True)
class BuildResult:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    profile: Profile | None = None
    plan: Plan | None = None
    files: dict[str, bytes] = field(default_factory=dict)
    sources: list[SourceState] = field(default_factory=list)
    collection_members: dict[str, list[Member]] = field(default_factory=dict)
    filtered: list[FilteredRule] = field(default_factory=list)
    broad: list[FileListing] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not has_errors(self.diagnostics)


def relative(config: Config, path: Path) -> str:
    try:
        return path.relative_to(config.project_root).as_posix()
    except ValueError:
        return path.as_posix()


def load_inputs(config: Config, result: BuildResult) -> tuple[bytes, bytes] | None:
    try:
        rules_bytes = config.rules.read_bytes()
        groups_bytes = config.groups.read_bytes()
    except FileNotFoundError as exc:
        result.diagnostics.append(error(Code.CONFIG, f"找不到输入文件：{exc.filename}"))
        return None
    parsed = parse_profile(rules_bytes.decode("utf-8"), relative(config, config.rules))
    result.profile = parsed.profile
    result.diagnostics.extend(parsed.diagnostics)
    groups = validate_groups(groups_bytes.decode("utf-8"), relative(config, config.groups))
    result.diagnostics.extend(groups.diagnostics)
    for route in parsed.profile.routes:
        if not is_known_target(route.target, groups.names):
            result.diagnostics.append(
                error(
                    Code.GROUP_REFERENCE,
                    f"策略组 {route.target!r} 不在 groups.toml 中，也不是内置策略",
                    route.span,
                )
            )
    return rules_bytes, groups_bytes


def unique_sources(profile: Profile) -> list[tuple[str, SourceRef]]:
    seen: dict[str, SourceRef] = {}
    for collection in profile.collections.values():
        for ref in collection.sources:
            seen.setdefault(source_id(ref.url, ref.format, ref.exclude_types), ref)
    return list(seen.items())


def load_sources(config: Config, result: BuildResult, *, required: bool) -> None:
    assert result.profile is not None
    store = StateStore.open(config.state)
    for sid, ref in unique_sources(result.profile):
        status = store.statuses.get(sid)
        snapshot = store.load(sid)
        state = SourceState(
            sid,
            ref,
            snapshot,
            status.consecutive_failures if status else 0,
            status.first_failure if status else "",
            status.last_error if status else "",
        )
        result.sources.append(state)
        if snapshot is None and required:
            hint = "先运行 domainrouter_v2 fetch" if not state.last_error else state.last_error
            result.diagnostics.append(
                error(Code.SNAPSHOT_MISSING, f"来源没有任何可用快照：{ref.url}", ref.span, hint)
            )
        elif state.consecutive_failures:
            result.diagnostics.append(
                warning(
                    Code.SOURCE_STALE,
                    f"来源最近 {state.consecutive_failures} 次获取失败，使用上次成功的内容："
                    f"{ref.url}（{state.last_error}）",
                    ref.span,
                )
            )


BROAD_REPORT = "reports/broad-rules.md"


class Classifier:
    """按成员缓存判定结果：同一条规则常出现在多个来源和合集中。"""

    def __init__(self) -> None:
        self.policy = BreadthPolicy.load()
        self.cache: dict[Member, Verdict] = {}

    def __call__(self, member: Member) -> Verdict:
        verdict = self.cache.get(member)
        if verdict is None:
            verdict = self.cache[member] = self.policy.classify(member)
        return verdict


def collect_members(result: BuildResult) -> Classifier:
    """汇总每个合集的成员，并过滤上游中的 EXCESSIVE 规则（手写规则只提醒）。"""
    assert result.profile is not None
    classify = Classifier()
    snapshots = {s.sid: s.snapshot for s in result.sources}
    for name, collection in result.profile.collections.items():
        members: list[Member] = []
        for item in collection.items:
            if isinstance(item, LocalMember):
                members.append(item.member)
                verdict = classify(item.member)
                if verdict.level is Breadth.EXCESSIVE:
                    result.diagnostics.append(
                        warning(
                            Code.BROAD_RULE,
                            f"手写规则范围过大（{verdict.reason}），按原样保留："
                            f"{render_member(item.member)}",
                            item.span,
                        )
                    )
                continue
            snap = snapshots.get(source_id(item.url, item.format, item.exclude_types))
            if snap is None:
                continue
            for member in snap.members():
                verdict = classify(member)
                if verdict.level is Breadth.EXCESSIVE:
                    result.filtered.append(
                        FilteredRule(render_member(member), verdict, name, item.url)
                    )
                else:
                    members.append(member)
        result.collection_members[name] = members
    if result.filtered:
        result.diagnostics.append(
            warning(
                Code.BROAD_FILTERED,
                f"过滤了 {len(result.filtered)} 条范围过大的上游规则，详见 {BROAD_REPORT}",
            )
        )
    return classify


def broad_listing(result: BuildResult, classify: Classifier) -> list[FileListing]:
    """已发布规则文件中范围较大的条目，按文件列出。"""
    assert result.plan is not None and result.profile is not None
    listings: list[FileListing] = []
    for artifact in result.plan.artifacts.values():
        handwritten = {
            item.member
            for name in artifact.collections
            for item in result.profile.collections[name].locals
        }
        for partition in PARTITIONS:
            rules = tuple(
                ListedRule(render_member(m), verdict, m in handwritten)
                for m in artifact.members(partition)
                if (verdict := classify(m)).level is not Breadth.NARROW
            )
            if rules:
                listings.append(FileListing(artifact.path(partition), artifact.targets, rules))
    return sorted(listings, key=lambda listing: listing.path)


def build(config: Config, *, write: bool = True) -> BuildResult:
    result = BuildResult()
    inputs = load_inputs(config, result)
    if inputs is None or result.profile is None:
        return result
    rules_bytes, groups_bytes = inputs
    load_sources(config, result, required=True)
    if not result.ok:
        return result
    classify = collect_members(result)
    plan = build_plan(
        result.profile,
        result.collection_members,
        resource_url=config.resource_url,
        interval=config.interval_seconds,
        allow_empty=config.allow_empty_collections,
    )
    result.plan = plan
    result.diagnostics.extend(plan.diagnostics)
    if not result.ok:
        return result
    source_hashes = {
        s.sid: s.snapshot.content_sha256 for s in result.sources if s.snapshot is not None
    }
    result.broad = broad_listing(result, classify)
    result.files = render_outputs(
        plan,
        groups_bytes,
        {BROAD_REPORT: render_listing(result.filtered, result.broad)},
        inputs={
            "rules": sha256(rules_bytes),
            "groups": sha256(groups_bytes),
            "sources": dict(sorted(source_hashes.items())),
        },
        settings={"base_url": config.base_url, "interval_seconds": config.interval_seconds},
        repository=config.repository_url,
    )
    if write:
        write_tree(config.output, result.files)
    return result


def write_tree(target: Path, files: dict[str, bytes]) -> None:
    """在同级临时目录写完整套文件，再替换目标目录；失败时旧目录保持不变。"""
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        for relative_path, data in files.items():
            path = staging / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        backup = target.with_name(f".{target.name}.old")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.rename(backup)
        staging.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def inline_dns_routes(profile: Profile) -> list[str]:
    """会在匹配阶段触发 DNS 解析的手写内联规则（只报告，不改写，decisions/0001 #8）。"""
    out: list[str] = []
    for route in profile.routes:
        if route.kind is RouteKind.INLINE and route.condition is not None:
            text = route.inline_text
            head = text.split(",", 1)[0]
            if head in {"GEOIP", "IP-CIDR", "IP-CIDR6", "IP-ASN", "IP-SUFFIX"} and (
                not text.endswith(",no-resolve")
            ):
                out.append(f"{text}: {route.target}")
    return out
