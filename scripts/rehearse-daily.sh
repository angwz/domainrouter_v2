#!/usr/bin/env bash
# 每日流程本地演练（规范 A01–A06）：本地裸仓库代替 GitHub 远端，本机 HTTP 服务代替上游。
# 与 GitHub Actions 调用同一组脚本（daily-build.sh / daily-publish.sh），逐个场景断言结果。
# 用法：scripts/rehearse-daily.sh [工作目录，默认 .cache/rehearsal]
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
work="${1:-$repo/.cache/rehearsal}"
port=18081
rm -rf "$work"
mkdir -p "$work/upstream"
remote="$work/remote.git"
git init -q --bare "$remote"

# ---- 演练用 profile：最小示例 + 两个本机上游来源 ----
project="$work/project"
cp -r "$repo/examples/minimal" "$project"
rm -rf "$project/dist" "$project/.cache"
cat >> "$project/my.wei" <<EOF

[Upstream]
@source http://127.0.0.1:$port/a.txt format=surge-domainset
@source http://127.0.0.1:$port/b.list format=surge
EOF
sed -i 's/^MATCH: /Upstream: 🧭 Proxy\nMATCH: /' "$project/my.wei"
printf 'alpha.example\n.beta.example\ngamma.example\ndelta.example\n' > "$work/upstream/a.txt"
printf 'DOMAIN-SUFFIX,one.example,DIRECT\nDOMAIN-KEYWORD,twoexample,REJECT\nIP-CIDR,198.51.100.0/24,no-resolve\n' \
  > "$work/upstream/b.list"

(cd "$work/upstream" && exec uv run --project "$repo" python -m http.server "$port" --bind 127.0.0.1) \
  >"$work/http.log" 2>&1 &
server=$!
trap 'kill $server 2>/dev/null || true' EXIT
for _ in $(seq 50); do curl -sf "http://127.0.0.1:$port/a.txt" >/dev/null && break; sleep 0.2; done

export DR="uv run --project $repo --locked domainrouter_v2"
export VERIFY_LEVEL="${VERIFY_LEVEL:-semantic}"
export CONFIG=config/domainrouter_v2.toml STATE_DIR=.cache/domainrouter_v2 OUT_DIR=out
unset GITHUB_STEP_SUMMARY

head_of() { git --git-dir="$remote" rev-parse --verify -q "refs/heads/$1" || echo none; }
run_day() {
  (cd "$project" && "$repo/scripts/daily-build.sh" "$remote" && "$repo/scripts/daily-publish.sh" "$remote" out "演练")
}
# 期望成功的一天：失败时打印日志末尾再退出，避免 set -e 静默中止
day() {
  if ! run_day >"$work/day$1.log" 2>&1; then
    echo "  ✗ 第 $1 天的流程意外失败，日志末尾："
    tail -n 20 "$work/day$1.log" | sed 's/^/    /'
    exit 1
  fi
}
has() { grep -q "$1" "$2" && echo yes || echo no; }
expect() { if [ "$1" = "$2" ]; then echo "  ✓ $3"; else echo "  ✗ $3（期望 $2，实际 $1）"; exit 1; fi; }

echo "== 场景 1：首次运行，发布完整内容"
day 1
r1="$(head_of release)"; s1="$(head_of state)"
expect "$([ "$r1" != none ] && echo yes)" yes "release 分支已创建"
expect "$(git --git-dir="$remote" show release:rulesets.toml | grep -c 'clash-domain/Upstream.yaml')" 1 "rulesets.toml 引用 Upstream"
git --git-dir="$remote" show release:clash-domain/Upstream.yaml > "$work/up1.yaml"
expect "$(grep -c "'+.beta.example'" "$work/up1.yaml")" 1 "DOMAIN-SET 前导点按 Surge 语义转为 +."

echo "== 场景 2：上游无变化，不制造空提交"
day 2
expect "$(head_of release)" "$r1" "release 无新提交"
expect "$(head_of state)" "$s1" "state 无新提交"
expect "$(has '内容未变化，未改动' "$work/day2.log")" yes "publish 判定内容未变"

echo "== 场景 3：上游新增条目，发布新版本并写更新说明"
printf 'epsilon.example\n' >> "$work/upstream/a.txt"
day 3
r3="$(head_of release)"
expect "$([ "$r3" != "$r1" ] && echo yes)" yes "release 有新提交"
expect "$(git --git-dir="$remote" show release:reports/latest.md | grep -c 'epsilon.example')" 1 "更新说明列出新增条目"

echo "== 场景 4：来源返回 404，沿用上次成功的副本"
mv "$work/upstream/b.list" "$work/upstream/b.list.bak"
day 4
expect "$(head_of release)" "$r3" "规则内容未变，release 无新提交"
expect "$(git --git-dir="$remote" show state:status.json | grep -c '"consecutive_failures": 1')" 1 "state 记录连续失败 1 次"
expect "$(has 'HTTP 404' "$work/day4.log")" yes "fetch 报告 HTTP 404"
mv "$work/upstream/b.list.bak" "$work/upstream/b.list"

echo "== 场景 5：来源内容骤降超过一半，视为异常并沿用旧副本"
printf 'alpha.example\n' > "$work/upstream/a.txt"
day 5
expect "$(has '骤降' "$work/day5.log")" yes "fetch 识别缩水异常"
git --git-dir="$remote" show release:clash-domain/Upstream.yaml > "$work/up5.yaml"
expect "$(grep -c "'epsilon.example'" "$work/up5.yaml")" 1 "发布内容保留旧副本中的条目"

echo "== 场景 6：新增来源首次即失败（无旧副本），整次失败且不发布"
before="$(head_of release)"
sed -i "s|^@source http://127.0.0.1:$port/b.list format=surge|&\n@source http://127.0.0.1:$port/missing.txt format=surge-domainset|" "$project/my.wei"
if run_day >"$work/day6.log" 2>&1; then echo "  ✗ 期望失败"; exit 1; fi
expect "$(head_of release)" "$before" "release 保持上一版"
expect "$(has '没有上次成功的副本' "$work/day6.log")" yes "明确提示没有可用副本"

echo "全部场景通过。日志：$work/day*.log"
