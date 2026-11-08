"""命令行入口：``domainrouter_v2 <命令>``。所有命令调用同一套库函数。

退出码（规范 §14）：0 成功；2 输入或配置错误；3 来源或快照错误；4 验证失败；1 内部错误。
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from domainrouter_v2 import __version__
from domainrouter_v2.build import (
    BuildResult,
    build,
    collect_members,
    load_inputs,
    load_sources,
    unique_sources,
)
from domainrouter_v2.config import Config, ConfigError, load_config
from domainrouter_v2.diagnostics import Code, Diagnostic, Level
from domainrouter_v2.publish import stage_release
from domainrouter_v2.report import make_report
from domainrouter_v2.sources.fetch import fetch_all
from domainrouter_v2.sources.snapshot import StateStore

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INPUT = 2
EXIT_SOURCE = 3
EXIT_VERIFY = 4

_SOURCE_CODES = {Code.SOURCE_FETCH, Code.SOURCE_FORMAT, Code.SNAPSHOT_MISSING}
DEFAULT_CONFIG = Path("config/domainrouter_v2.toml")


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.out is not None:
            config = _with_output(config, args.out)
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return EXIT_INPUT
    handler = args.handler
    code: int = handler(config, args)
    return code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="domainrouter_v2",
        description="把 my.wei 与上游规则编译为优化后的 Mihomo 规则集与 subconverter TOML。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(required=True, metavar="<命令>")

    def command(name: str, help_text: str) -> argparse.ArgumentParser:
        cmd = sub.add_parser(name, help=help_text, description=help_text)
        cmd.add_argument(
            "--config",
            type=Path,
            default=DEFAULT_CONFIG,
            help=f"构建配置文件（默认 {DEFAULT_CONFIG.as_posix()}）",
        )
        cmd.add_argument("--out", type=Path, default=None, help="覆盖输出目录（不改变发布地址）")
        cmd.add_argument("-v", "--verbose", action="store_true", help="同时显示 info 级诊断")
        return cmd

    check = command("check", "检查 my.wei、groups.toml 与配置；有快照时一并检查来源")
    check.set_defaults(handler=_check)
    fetch = command("fetch", "联网获取全部上游来源，健康检查通过后更新快照")
    fetch.set_defaults(handler=_fetch)
    build_cmd = command("build", "只用本地快照构建规则文件与 TOML（不联网）")
    build_cmd.set_defaults(handler=_build)
    publish = command("publish", "构建并把整套产物与更新说明放进 release 目录（无变化时不改动）")
    publish.add_argument("--release-dir", type=Path, required=True, help="release 分支的工作目录")
    publish.add_argument(
        "--summary", type=Path, default=None, help="另存一份更新说明（如 $GITHUB_STEP_SUMMARY）"
    )
    publish.set_defaults(handler=_publish)
    return parser


def _with_output(config: Config, out: Path) -> Config:
    return replace(config, output=out.resolve())


def _print_diagnostics(diagnostics: list[Diagnostic], verbose: bool) -> None:
    for diagnostic in diagnostics:
        if diagnostic.level is Level.INFO and not verbose:
            continue
        stream = sys.stderr if diagnostic.level is Level.ERROR else sys.stdout
        print(diagnostic.render(), file=stream)


def _exit_code(result: BuildResult) -> int:
    errors = [d for d in result.diagnostics if d.level is Level.ERROR]
    if not errors:
        return EXIT_OK
    if all(d.code in _SOURCE_CODES for d in errors):
        return EXIT_SOURCE
    return EXIT_INPUT


def _summary(result: BuildResult) -> str:
    errors = sum(d.level is Level.ERROR for d in result.diagnostics)
    warnings = sum(d.level is Level.WARNING for d in result.diagnostics)
    return f"{errors} 个错误，{warnings} 个警告"


def _check(config: Config, args: argparse.Namespace) -> int:
    result = BuildResult()
    if load_inputs(config, result) is None or result.profile is None:
        _print_diagnostics(result.diagnostics, args.verbose)
        return EXIT_INPUT
    load_sources(config, result, required=False)
    collect_members(result)
    _print_diagnostics(result.diagnostics, args.verbose)
    profile = result.profile
    missing = sum(1 for s in result.sources if s.snapshot is None)
    print(
        f"合集 {len(profile.collections)} 个，路由 {len(profile.routes)} 条，"
        f"来源 {len(result.sources)} 个（{missing} 个尚无快照）；{_summary(result)}"
    )
    if missing:
        print("注意：缺少快照的来源未检查，结果为部分检查（partial）。")
    return _exit_code(result)


def _fetch(config: Config, args: argparse.Namespace) -> int:
    result = BuildResult()
    if load_inputs(config, result) is None or result.profile is None:
        _print_diagnostics(result.diagnostics, args.verbose)
        return EXIT_INPUT
    refs = [ref for _, ref in unique_sources(result.profile)]
    store = StateStore.open(config.state)
    outcomes = fetch_all(refs, store, config.fetch)
    failed = 0
    for outcome in outcomes:
        mark = "✓" if outcome.ok else "✗"
        print(f"{mark} {outcome.ref.url}  {outcome.message}")
        if not outcome.ok:
            failed += 1
            if store.load(outcome.sid) is None:
                print("  ↳ 没有上次成功的副本，构建将失败", file=sys.stderr)
    print(f"来源 {len(outcomes)} 个，失败 {failed} 个；快照目录 {config.state}")
    no_fallback = any(not o.ok and store.load(o.sid) is None for o in outcomes)
    return EXIT_SOURCE if no_fallback else EXIT_OK


def _build(config: Config, args: argparse.Namespace) -> int:
    result = build(config)
    _print_diagnostics(result.diagnostics, args.verbose)
    if not result.ok:
        print(f"构建失败：{_summary(result)}；输出目录未改动", file=sys.stderr)
        return _exit_code(result)
    assert result.plan is not None
    files = [path for path in result.files if path.endswith(".yaml")]
    print(
        f"已写出 {len(files)} 个规则文件、rulesets.toml（{len(result.plan.rulesets)} 条）、"
        f"groups.toml 到 {config.output}；{_summary(result)}"
    )
    return EXIT_OK


def _publish(config: Config, args: argparse.Namespace) -> int:
    result = build(config)
    _print_diagnostics(result.diagnostics, args.verbose)
    if not result.ok:
        print(f"构建失败：{_summary(result)}；release 目录未改动", file=sys.stderr)
        return _exit_code(result)
    release_dir: Path = args.release_dir.resolve()
    previous = release_dir if release_dir.is_dir() else None
    report = make_report(config, result, previous, datetime.now(UTC))
    changed = stage_release(release_dir, result.files, report)
    if args.summary is not None:
        with args.summary.open("ab") as handle:
            handle.write(report.to_markdown())
    state = "已更新" if changed else "内容未变化，未改动"
    print(f"release 目录 {release_dir}：{state}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
