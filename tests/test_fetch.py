"""来源获取与健康检查（merge-cases §8，规范 B03、A02），使用本地伪造传输，不联网。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from domainrouter_v2.config import FetchConfig
from domainrouter_v2.diagnostics import SourceSpan
from domainrouter_v2.model.profile import SourceRef
from domainrouter_v2.sources.fetch import fetch_all
from domainrouter_v2.sources.snapshot import StateStore, decode_member, encode_member, source_id

URL = "https://example.org/list.txt"
CONFIG = FetchConfig(max_attempts=1)
NOW = datetime(2026, 11, 8, tzinfo=UTC)


def ref(fmt: str = "surge") -> SourceRef:
    return SourceRef(URL, fmt, SourceSpan("my.wei", 1))


def serve(status: int, body: bytes, headers: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    calls: list[dict[str, str]] = []

    def get(url: str, request_headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        calls.append(request_headers)
        return status, headers or {}, body

    get.calls = calls  # type: ignore[attr-defined]
    return get


def run(tmp_path: Path, transport, fmt: str = "surge"):  # type: ignore[no-untyped-def]
    store = StateStore.open(tmp_path)
    outcome = fetch_all([ref(fmt)], store, CONFIG, transport, now=lambda: NOW)[0]
    return outcome, StateStore.open(tmp_path)


GOOD = b"DOMAIN-SUFFIX,a.com\nDOMAIN,b.com\nIP-CIDR,1.0.0.0/8,no-resolve\n"


def test_success_writes_sorted_snapshot(tmp_path: Path) -> None:
    outcome, store = run(tmp_path, serve(200, GOOD, {"ETag": '"v1"'}))
    assert outcome.ok and outcome.changed
    snapshot = store.load(outcome.sid)
    assert snapshot is not None
    assert snapshot.lines == ["d +.a.com", "d b.com", "n 1.0.0.0/8"]
    assert store.statuses[outcome.sid].etag == '"v1"'


def test_unchanged_content_is_not_changed(tmp_path: Path) -> None:
    run(tmp_path, serve(200, GOOD))
    outcome, _ = run(tmp_path, serve(200, GOOD))
    assert outcome.ok and not outcome.changed


def test_conditional_request_and_304(tmp_path: Path) -> None:
    run(tmp_path, serve(200, GOOD, {"ETag": '"v1"'}))
    transport = serve(304, b"")
    outcome, _ = run(tmp_path, transport)
    assert outcome.ok and outcome.not_modified
    assert transport.calls[0]["If-None-Match"] == '"v1"'


def test_304_without_snapshot_is_failure(tmp_path: Path) -> None:
    outcome, store = run(tmp_path, serve(304, b""))
    assert not outcome.ok
    assert store.load(outcome.sid) is None


def assert_failure_keeps_previous(tmp_path: Path, transport) -> str:  # type: ignore[no-untyped-def]
    first, _ = run(tmp_path, serve(200, GOOD))
    outcome, store = run(tmp_path, transport)
    assert not outcome.ok
    snapshot = store.load(first.sid)
    assert snapshot is not None and len(snapshot.lines) == 3
    status = store.statuses[first.sid]
    assert status.consecutive_failures == 1 and status.first_failure
    return outcome.message


def test_http_error_keeps_previous(tmp_path: Path) -> None:
    assert "HTTP 404" in assert_failure_keeps_previous(tmp_path, serve(404, b"no"))


def test_html_keeps_previous(tmp_path: Path) -> None:
    message = assert_failure_keeps_previous(tmp_path, serve(200, b"<!DOCTYPE html><html>x</html>"))
    assert "HTML" in message


def test_empty_keeps_previous(tmp_path: Path) -> None:
    assert "空响应" in assert_failure_keeps_previous(tmp_path, serve(200, b"\n  \n"))


def test_shrink_keeps_previous(tmp_path: Path) -> None:
    message = assert_failure_keeps_previous(tmp_path, serve(200, b"DOMAIN,b.com\n"))
    assert "骤降" in message


def test_binary_keeps_previous(tmp_path: Path) -> None:
    assert "UTF-8" in assert_failure_keeps_previous(tmp_path, serve(200, b"\xff\xfe\x00bin"))


def test_too_many_invalid_lines(tmp_path: Path) -> None:
    body = b"DOMAIN,a.com\n" + b"garbage line\n" * 5
    outcome, _ = run(tmp_path, serve(200, body))
    assert not outcome.ok and "写法错误" in outcome.message


def test_recovery_resets_failures(tmp_path: Path) -> None:
    run(tmp_path, serve(200, GOOD))
    run(tmp_path, serve(500, b""))
    outcome, store = run(tmp_path, serve(200, GOOD))
    assert outcome.ok
    assert store.statuses[outcome.sid].consecutive_failures == 0


def test_duplicate_refs_fetched_once(tmp_path: Path) -> None:
    transport = serve(200, GOOD)
    store = StateStore.open(tmp_path)
    outcomes = fetch_all([ref(), ref()], store, CONFIG, transport, now=lambda: NOW)
    assert len(outcomes) == 1 and len(transport.calls) == 1


def test_member_codec_roundtrip() -> None:
    for line in [
        "d +.a.com",
        "d *.b.com",
        "n 2001:db8::/32",
        "c GEOIP,CN,no-resolve",
        "c AND,((DOMAIN,a.com),(NETWORK,UDP))",
        "c DOMAIN-REGEX,^a,b$",
    ]:
        assert encode_member(decode_member(line)) == line


def test_source_id_depends_on_format() -> None:
    assert source_id(URL, "surge") != source_id(URL, "domain")
