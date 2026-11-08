#!/usr/bin/env bash
# 用法：push-branch.sh <远端地址> <分支> <内容目录> <提交说明>
# 以内容目录作为分支的完整内容提交，并在远端当前提交之上快进推送。
# 内容未变化时不提交（不制造空提交）；从不强推，远端被并发改动时推送失败并返回非零。
set -euo pipefail
remote="$1" branch="$2" content="$3" message="$4"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git -C "$work" init -q
if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
  git -C "$work" fetch -q --depth=1 "$remote" "refs/heads/$branch"
  git -C "$work" checkout -q -B "$branch" FETCH_HEAD
else
  git -C "$work" checkout -q --orphan "$branch"
fi
find "$work" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
(cd "$content" && tar -cf - --exclude=./.git .) | tar -xf - -C "$work"
git -C "$work" add -A
if git -C "$work" diff --cached --quiet; then
  echo "$branch：内容未变化，不提交"
  exit 0
fi
git -C "$work" \
  -c user.name="github-actions[bot]" \
  -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
  commit -q -m "$message"
git -C "$work" push -q "$remote" "HEAD:refs/heads/$branch"
echo "$branch：已推送 $(git -C "$work" rev-parse --short HEAD)"
