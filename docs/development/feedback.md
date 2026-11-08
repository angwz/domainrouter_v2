# 用户意见记录

> 按时间顺序记录用户对本项目提出的每一条意见，以及处理结果。每收到新意见就追加一条，已有条目只更新「处理」列，不改写原意。
> 原话尽量照录（「」内），较长的意见做摘要。已形成正式决定的，以 [docs/decisions/](../decisions/) 为准。

状态：✅ 已实现 · 🔄 部分实现 / 进行中 · 🕓 计划中 · ➖ 不做（附原因）

## 2026-11-08 · 项目启动与范围

| # | 意见 | 处理 | 位置 |
| --- | --- | --- | --- |
| 1 | 每日自动生成三类规则集是核心必需；Web 与 AI 暂不实施 | ✅ 每日工作流 HKT 04:17 + 手动触发 | [daily-automation](../daily-automation.md) |
| 2 | 「上游改了规则是自然的……所以才设置每天更新一次」：上游每天跟随变化，不冻结 | ✅ 来源锁只作收据 | [0001](../decisions/0001-deviations-from-spec-1.5.md) #4 |
| 3 | 「合并和精简是本项目的重点，要从 clash 的匹配效率出发……总体目标是 clash 的匹配效率最优」 | ✅ 按 Mihomo 真实数据结构优化，并实测 | [merge-cases §1](../rules/merge-cases.md)、[performance](../performance.md) |
| 4 | MRS 不是重点，先生成 YAML；麻烦的话以后再做 | 🕓 推迟；放置方式已定（见 2026-11-09 #20） | [0001](../decisions/0001-deviations-from-spec-1.5.md) #1 |
| 5 | 「没需求不要创造需求」：不要 base 和 external-config.toml | ✅ 只生成 rulesets.toml、groups.toml | [0001](../decisions/0001-deviations-from-spec-1.5.md) #2 |
| 6 | 写合并规则案例文档，尽可能覆盖边界情况，保证合并有效 | ✅ 每个案例对应测试 | [merge-cases](../rules/merge-cases.md) |
| 7 | 来源格式按各工具官方文档转换；没有官方文档的舍弃 | ✅ 不支持 Quantumult X | [0001](../decisions/0001-deviations-from-spec-1.5.md) #6 |
| 8 | 上游自带的策略字段（含 `REJECT`）与参数是无效信息，预处理掉；策略由自己在 groups.toml 决定 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #7 |
| 9 | 无法安全转换的规则，用现代化方式在每次更新说明中写明 | ✅ `reports/latest.md` | [report.py](../../src/domainrouter_v2/report.py) |
| 10 | 「不要太借鉴老项目的……应该多借鉴互联网，进行现代化构思」 | ✅ 处理方案依据官方文档与现代项目 | [0001](../decisions/0001-deviations-from-spec-1.5.md) |
| 11 | 对广告不敏感：「规则放哪块，就是我想要的哪块」，不做广告列表提醒；以后由 AI 给建议 | ✅ 不做提醒；AI 🕓 | [0001](../decisions/0001-deviations-from-spec-1.5.md) |
| 12 | 末尾的 `GEOIP,CN: DIRECT` 不带 no-resolve 是刻意的：「按我写的原样保留吧」 | ✅ 手写规则原样保留 | [0001](../decisions/0001-deviations-from-spec-1.5.md) #8 |
| 13 | 工程质量：审美克制清晰；README 简洁、细节进 docs；模块清晰、无死代码、不吞异常；文档与代码同步；CLAUDE.md、progress.md、decisions；小步交付并自查 | ✅ 长期有效 | [CLAUDE.md](../../CLAUDE.md) |
| 14 | 来源失败：「用上次的副本吧，久了还没有……在该提示我的地方提示我这个没有了就行」 | ✅ 沿用旧副本；超过 7 天在更新说明顶部提示 | [0001](../decisions/0001-deviations-from-spec-1.5.md) #5 |
| 15 | rulesets 数量不设上限，按当前需求生成；少一点也好；my.wei 随时会改，要灵活 | ✅ 相邻同目标合集合并成一组文件 | [merge-cases §9](../rules/merge-cases.md) |
| 16 | 开始前问过：不需要先在 GitHub 创建仓库等准备吗？ | ➖ 按约定暂不创建远端，列为 M4b | [daily-automation](../daily-automation.md) |

## 2026-11-09 · 交付后的意见

| # | 意见 | 处理 | 位置 |
| --- | --- | --- | --- |
| 17 | 过滤 `DOMAIN-KEYWORD,ads` 这类太宽泛的关键词，维护一个从互联网收集的词表；`DOMAIN-KEYWORD,google` 这类「很可怕」，在单独的 md 中提醒发布了哪些；其他容易宽泛的规则也要提醒；「像 0.0.0.0/0 这类，有的话也应该被过滤！！！」 | ✅ 上游过宽规则过滤，宽泛规则列入 `reports/broad-rules.md`；手写规则只提醒 | [0002](../decisions/0002-filter-broad-upstream-rules.md)、[broad-rules](../rules/broad-rules.md) |
| 18 | v1 的 release 已重跑恢复；64 条上限的问题「不用管」 | ✅ 迁移报告已更新；构建时仍保留提示 | [v1-report](../migration/v1-report.md) |
| 19 | YAML 文件头「不够优雅简洁，太丑了」，v1 的更好；domain 排序要更讲究：`+.` 一级按字母，再二级……再 `*` 通配，单个主机名放底部 | ✅ `# KEY: value` 文件头；按覆盖范围从宽到窄排列；UPDATED 只随内容变化 | [merge-cases §10](../rules/merge-cases.md#10-规则文件的排列与文件头) |
| 20 | 「我个人对审美要求偏高」，排序等是为了自己看着舒服；以后还会多次对合并排序提意见 | ✅ 记为长期偏好 | 本文件 |
| 21 | 给 YAML 每条规则加同行注释：来自哪个上游、覆盖了哪些上游规则，方便检查合并算法；注释要兼顾审美 | ✅ 来源图例 + 对齐的同行注释；`explain --rule` 看完整来历；文件体积 +67%，Mihomo 加载时间无可测变化 | [merge-cases §10](../rules/merge-cases.md#10-规则文件的排列与文件头) |
| 22 | 以后增加 MRS：放在 YAML 同目录还是更规范的位置？MRS 无法预览，无需注释，只要程序能读懂 | 🕓 计划：与 YAML 同目录、同名、扩展名 `.mrs`（MetaCubeX/meta-rules-dat 的做法）；只做 domain 与 ipcidr（Mihomo 的 MRS 不支持 classical）；不含注释 | — |
| 23 | 单独维护一个文件，记录提过的每条意见，方便 Claude 以后继续，也方便自己查看 | ✅ 本文件；CLAUDE.md 要求每次追加 | 本文件 |
