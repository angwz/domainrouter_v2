#!/usr/bin/env bash
# 用法：pull-branch.sh <远端地址> <分支> <目标目录>
# 把远端分支的完整内容导出到目标目录（不带 .git）；分支不存在时得到空目录。只读操作。
set -euo pipefail
remote="$1" branch="$2" target="$3"
mkdir -p "$target"
if ! git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
  echo "$branch：远端尚无此分支，从空目录开始"
  exit 0
fi
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git -C "$work" init -q
git -C "$work" fetch -q --depth=1 "$remote" "refs/heads/$branch"
git -C "$work" archive FETCH_HEAD | tar -x -C "$target"
echo "$branch：已导出 $(git -C "$work" rev-parse --short FETCH_HEAD) 到 $target"
