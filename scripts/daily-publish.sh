#!/usr/bin/env bash
# 每日流程的发布阶段：把已验证的暂存内容快进推送到 release 与 state 分支。
# 用法：daily-publish.sh <远端地址> [暂存目录，默认 out] [运行标识]
# 内容未变化的分支不提交；从不强推。
set -euo pipefail
remote="$1"
staged="${2:-out}"
run="${3:-local}"
here="$(cd "$(dirname "$0")" && pwd)"
# 提交信息用北京时间的日期：定时运行在 UTC 22:00，若用 UTC 会显示为前一天。
# 不依赖系统时区数据库，直接用固定的 UTC+8 偏移（中国不实行夏令时）。
day="$(date -u -d "@$(( $(date -u +%s) + 8 * 3600 ))" +%Y-%m-%d)"
"$here/push-branch.sh" "$remote" release "$staged/release" "rules: $day 每日生成（$run）"
"$here/push-branch.sh" "$remote" state "$staged/state" "state: $day 来源快照（$run）"
