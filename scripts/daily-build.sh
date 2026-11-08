#!/usr/bin/env bash
# 每日流程的只读阶段：恢复快照 → 刷新上游 → 检查 → 验证 → 构建并暂存发布内容。
# 用法：daily-build.sh <远端地址>
# 环境变量（均有默认值）：
#   DR            调用命令，默认 "uv run --locked domainrouter_v2"
#   CONFIG        构建配置，默认 config/domainrouter_v2.toml
#   STATE_DIR     快照目录，需与配置中的 paths.state 一致，默认 .cache/domainrouter_v2
#   OUT_DIR       暂存目录，默认 out（release/ 与 state/ 两个子目录）
#   VERIFY_LEVEL  kernel（默认，需准备工具）或 semantic
# 任一步失败即以非零退出，暂存目录不会被当作可发布内容。
set -euo pipefail
remote="$1"
here="$(cd "$(dirname "$0")" && pwd)"
DR="${DR:-uv run --locked domainrouter_v2}"
CONFIG="${CONFIG:-config/domainrouter_v2.toml}"
STATE_DIR="${STATE_DIR:-.cache/domainrouter_v2}"
OUT_DIR="${OUT_DIR:-out}"
VERIFY_LEVEL="${VERIFY_LEVEL:-kernel}"
SUMMARY="${GITHUB_STEP_SUMMARY:-$OUT_DIR/summary.md}"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
"$here/pull-branch.sh" "$remote" state "$STATE_DIR"
$DR fetch --config "$CONFIG"
$DR check --config "$CONFIG"
if [ "$VERIFY_LEVEL" = kernel ]; then
  $DR tools prepare --config "$CONFIG"
fi
$DR verify --config "$CONFIG" --level "$VERIFY_LEVEL"
"$here/pull-branch.sh" "$remote" release "$OUT_DIR/release"
$DR publish --config "$CONFIG" --release-dir "$OUT_DIR/release" --summary "$SUMMARY"
mkdir -p "$OUT_DIR/state"
cp -a "$STATE_DIR/sources" "$STATE_DIR/status.json" "$OUT_DIR/state/"
echo "暂存完成：$OUT_DIR"
