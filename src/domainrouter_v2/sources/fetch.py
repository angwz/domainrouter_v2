"""下载上游来源、健康检查，并在成功时更新快照（项目中唯一联网的模块）。

一个来源被判为「本次失败」的情况（merge-cases §8）：
网络错误或非 2xx、响应超限、不是 UTF-8 文本、HTML 页面、空内容、整份格式错误、
写法错误行比例过高、条目数比上次成功缩水超过阈值。
失败时保留上次成功的快照（构建会使用它并在报告中告警），只更新健康记录。
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from domainrouter_v2 import __version__
from domainrouter_v2.config import FetchConfig
from domainrouter_v2.model.profile import SourceRef
from domainrouter_v2.parse.formats import ParseResult, SourceFormatError, parse_source
from domainrouter_v2.parse.freeline import FreeLineError, convert_free_line
from domainrouter_v2.sources.net import make_transport
from domainrouter_v2.sources.snapshot import (
    SnapshotMeta,
    SourceStatus,
    StateStore,
    make_snapshot,
    source_id,
)

USER_AGENT = f"domainrouter_v2/{__version__} (+https://github.com/angwz/domainrouter_v2)"


class FetchFailure(Exception):
    pass


@dataclass(slots=True)
class FetchOutcome:
    sid: str
    ref: SourceRef
    ok: bool
    message: str
    entries: int = 0
    changed: bool = False
    not_modified: bool = False


type Transport = Callable[[str, dict[str, str]], tuple[int, dict[str, str], bytes]]


def http_transport(config: FetchConfig) -> Transport:
    """真实网络传输；测试中可替换为本地函数。"""
    timeout = httpx.Timeout(
        config.total_timeout_seconds,
        connect=config.connect_timeout_seconds,
        read=config.read_timeout_seconds,
    )

    def get(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        with (
            httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                max_redirects=5,
                transport=make_transport(),
            ) as client,
            client.stream("GET", url, headers={"User-Agent": USER_AGENT, **headers}) as resp,
        ):
            if resp.url.scheme not in {"http", "https"}:
                raise FetchFailure(f"重定向到不支持的协议：{resp.url.scheme}")
            chunks: list[bytes] = []
            size = 0
            for chunk in resp.iter_bytes():
                size += len(chunk)
                if size > config.max_response_bytes:
                    raise FetchFailure(f"响应超过 {config.max_response_bytes} 字节上限")
                chunks.append(chunk)
            return resp.status_code, dict(resp.headers), b"".join(chunks)

    return get


def fetch_all(
    refs: list[SourceRef],
    store: StateStore,
    config: FetchConfig,
    transport: Transport | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> list[FetchOutcome]:
    """并发获取全部去重后的来源；结果按声明顺序返回，与完成顺序无关。"""
    get = transport or http_transport(config)
    unique: dict[str, SourceRef] = {}
    for ref in refs:
        unique.setdefault(source_id(ref.url, ref.format, ref.exclude_types), ref)
    # 健康记录在主线程预先建立，工作线程只修改各自的记录
    for sid, ref in unique.items():
        store.statuses.setdefault(sid, SourceStatus(ref.url, ref.format))
    with ThreadPoolExecutor(max_workers=config.max_workers) as pool:
        futures = {
            sid: pool.submit(_fetch_one, sid, ref, store, config, get, now)
            for sid, ref in unique.items()
        }
        outcomes = [futures[sid].result() for sid in unique]
    store.save_statuses()
    return outcomes


def _fetch_one(
    sid: str,
    ref: SourceRef,
    store: StateStore,
    config: FetchConfig,
    get: Transport,
    now: Callable[[], datetime],
) -> FetchOutcome:
    status = store.statuses[sid]
    stamp = now().isoformat(timespec="seconds")
    previous = store.load(sid)
    headers: dict[str, str] = {}
    if previous is not None and status.raw_sha256 == previous.meta.raw_sha256:
        if status.etag:
            headers["If-None-Match"] = status.etag
        if status.last_modified:
            headers["If-Modified-Since"] = status.last_modified
    try:
        code, response_headers, body = _download(ref.url, headers, config, get)
        if code == 304 and previous is not None:
            _mark_success(status)
            return FetchOutcome(
                sid, ref, True, "未变化（HTTP 304）", previous.meta.entries, not_modified=True
            )
        result, detected = _parse(body, ref)
        _check_health(result, previous.meta.entries if previous else None, config)
    except FetchFailure as exc:
        status.consecutive_failures += 1
        status.first_failure = status.first_failure or stamp
        status.last_error = str(exc)
        return FetchOutcome(sid, ref, False, str(exc))

    raw_sha = hashlib.sha256(body).hexdigest()
    meta = SnapshotMeta(
        url=ref.url,
        format=ref.format,
        detected_format=detected,
        raw_sha256=raw_sha,
        fetched_at=stamp,
        entries=len(result.entries),
        skipped=len(result.skipped),
        invalid=sum(1 for s in result.skipped if s.invalid),
    )
    snapshot = make_snapshot(meta, [e.member for e in result.entries])
    changed = previous is None or previous.lines != snapshot.lines
    if changed:
        # 只在成员变化时改写快照：抓取时间等元数据不应让 state 分支每天产生提交
        store.save(sid, snapshot)
        _write_skipped(store, sid, result)
    status.etag = response_headers.get("etag", "")
    status.last_modified = response_headers.get("last-modified", "")
    status.raw_sha256 = raw_sha
    _mark_success(status)
    return FetchOutcome(
        sid, ref, True, "已更新" if changed else "内容未变", len(snapshot.lines), changed=changed
    )


def _mark_success(status: SourceStatus) -> None:
    status.consecutive_failures = 0
    status.first_failure = ""
    status.last_error = ""


def _download(
    url: str, headers: dict[str, str], config: FetchConfig, get: Transport
) -> tuple[int, dict[str, str], bytes]:
    last_error = ""
    for attempt in range(config.max_attempts):
        try:
            code, response_headers, body = get(url, headers)
        except (httpx.HTTPError, OSError) as exc:
            last_error = f"网络错误：{type(exc).__name__}: {exc}"
        else:
            lowered = {k.lower(): v for k, v in response_headers.items()}
            if code == 304 or 200 <= code < 300:
                return code, lowered, body
            last_error = f"HTTP {code}"
            if 400 <= code < 500 and code != 429:
                break  # 客户端错误重试无意义
        if attempt + 1 < config.max_attempts:
            time.sleep(min(2**attempt, 8))
    raise FetchFailure(last_error)


def _parse(body: bytes, ref: SourceRef) -> tuple[ParseResult, str]:
    if not body.strip():
        raise FetchFailure("空响应")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FetchFailure(f"不是 UTF-8 文本（{exc.reason}）") from exc
    head = text[:2048].lstrip().lower()
    if head.startswith(("<!doctype html", "<html")):
        raise FetchFailure("返回的是 HTML 页面，不是规则")
    if ref.format == "wei":
        return _parse_wei(text), "wei"
    try:
        result = parse_source(text, ref.format, ref.exclude_types)
    except SourceFormatError as exc:
        raise FetchFailure(f"格式错误：{exc}") from exc
    return result, result.format


def _parse_wei(text: str) -> ParseResult:
    """远程 my.wei 风格列表：只接受自由行，不允许再引用 URL。"""
    result = ParseResult("wei")
    for number, raw in enumerate(text.removeprefix("﻿").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if line.startswith(("@", "[")) or "://" in line:
            result.skip(number, line, "远程 wei 列表不支持节、指令或嵌套 URL", invalid=True)
            continue
        try:
            converted = convert_free_line(line)
        except FreeLineError as exc:
            result.skip(number, line, exc.message, invalid=not exc.skip)
            continue
        result.add(converted.member, number, converted.notes)
    return result


def _check_health(result: ParseResult, previous: int | None, config: FetchConfig) -> None:
    entries = len(result.entries)
    invalid = sum(1 for s in result.skipped if s.invalid)
    total = entries + len(result.skipped)
    if entries == 0:
        raise FetchFailure("没有任何可用规则")
    if total and invalid / total > config.max_invalid_ratio:
        raise FetchFailure(f"写法错误的行占 {invalid}/{total}，疑似格式识别错误或上游异常")
    if previous and entries < previous * (1 - config.shrink_threshold):
        raise FetchFailure(f"条目数从 {previous} 骤降到 {entries}，疑似上游异常")


def _write_skipped(store: StateStore, sid: str, result: ParseResult) -> None:
    """跳过的条目单独记录，供更新说明引用；不参与构建。"""
    path = store.root / "sources" / f"{sid}.skipped.txt"
    lines = [
        f"{s.line}\t{'invalid' if s.invalid else 'skip'}\t{s.text}\t{s.reason}"
        for s in result.skipped
    ]
    path.write_bytes(("\n".join(lines) + "\n" if lines else "").encode("utf-8"))
