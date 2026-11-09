# 维护者意见

维护者对项目提出的每条意见及其处理结果，按时间排列，供维护者回顾、供后续接手的代理了解哪些方向已经讨论过。

- 每条意见用一句话概括其要求与动机，不摘录原话。
- 新意见追加在末尾，编号连续；处理有进展时只更新「状态」与「落点」。
- 已形成正式决定的，细节以 [decisions/](../decisions/) 为准。

**状态** ✅ 已完成 · 🔄 进行中 · 🕓 已规划 · ➖ 不采纳

## 立项（2026-11-08）

| # | 意见 | 状态 | 落点 |
| ---: | --- | :---: | --- |
| 1 | 每天自动生成三类规则集是核心功能；Web 与 AI 暂缓 | ✅ | [每日自动更新](../guide/daily-automation.md) |
| 2 | 上游每天跟随变化，来源锁只作记录，不冻结内容 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #4 |
| 3 | 合并与精简是项目重心，以 Mihomo 的匹配效率为最终目标 | ✅ | [merge-cases §1](../rules/merge-cases.md)、[性能](../design/performance.md) |
| 4 | MRS 不是重点，先输出 YAML | 🕓 | [0001](../decisions/0001-deviations-from-spec-1.5.md) #1，放置方式见 #22 |
| 5 | 不为假想需求增加产物：不生成 base 与 external-config | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #2 |
| 6 | 用案例文档覆盖合并的各种边界情况，并以测试保证 | ✅ | [merge-cases](../rules/merge-cases.md) |
| 7 | 来源格式只按官方文档转换；没有官方文档的格式不支持 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #6 |
| 8 | 上游的策略字段与参数一律剥离，策略只由 groups.toml 决定 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #7 |
| 9 | 无法安全转换的规则在每次更新说明中逐条说明 | ✅ | `reports/latest.md` |
| 10 | 设计参考现代项目与官方资料，而非沿用 v1 实现 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) |
| 11 | 规则放在哪个分组即代表意图，不做广告类提醒；修改建议留给日后的 AI 功能 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) |
| 12 | 手写规则按原样保留，包括刻意不带 `no-resolve` 的 `GEOIP,CN` | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #8 |
| 13 | 工程质量的长期标准：克制的呈现、清晰的模块、文档与代码同步、小步交付并自查 | ✅ | [CLAUDE.md](../../CLAUDE.md) |
| 14 | 来源失效时沿用上次的副本，长期失效只需提醒 | ✅ | [0001](../decisions/0001-deviations-from-spec-1.5.md) #5 |
| 15 | 规则集数量随 my.wei 变化，不设上限，能少则少 | ✅ | [merge-cases §9](../rules/merge-cases.md) |
| 16 | 开工前是否需要先在 GitHub 建仓库 | ➖ | 远端操作统一放到首次发布时 |

## 首次交付之后（2026-11-09）

| # | 意见 | 状态 | 落点 |
| ---: | --- | :---: | --- |
| 17 | 过滤 `ads`、`0.0.0.0/0` 这类范围过宽的上游规则，词表要有公开依据；品牌关键词等宽泛规则单独列清单提醒 | ✅ | [0002](../decisions/0002-filter-broad-upstream-rules.md)、[broad-rules](../rules/broad-rules.md) |
| 18 | v1 发布已恢复；subconverter 的 64 条上限不影响实际使用 | ✅ | [v1 迁移](../history/v1-migration.md) |
| 19 | 规则文件头应像 v1 一样简洁；domain 条目按 `+.` 层级 → 通配 → 精确主机名排列 | ✅ | [merge-cases §10](../rules/merge-cases.md#10-规则文件的排列与文件头) |
| 20 | 排列与注释首先服务于人工阅读，后续会持续调整合并与排序的呈现 | ✅ | 长期偏好 |
| 21 | 每条规则用同行注释标出来源，以及它合并、覆盖了哪些上游规则，便于审查合并算法 | ✅ | [merge-cases §10](../rules/merge-cases.md#10-规则文件的排列与文件头)、`explain --rule` |
| 22 | 将来的 MRS 放在哪里：与 YAML 同目录、同名，扩展名 `.mrs`；只做 domain 与 ipcidr；不含注释 | 🕓 | 实施 MRS 时执行 |
| 23 | 维护一份意见记录，便于双方回顾 | ✅ | 本文件 |
| 24 | 意见记录不引用原话，统一写成中性总结 | ✅ | 本文件 |
| 25 | 文档兼顾人与 AI 代理的阅读体验，可自由重组目录与段落 | ✅ | [文档地图](../README.md) |
| 26 | 准备首次发布到 GitHub | ✅ | [每日自动更新 · 首次启用](../guide/daily-automation.md#首次启用) |
| 27 | 许可证选定 GPL-3.0 | ✅ | [LICENSE](../../LICENSE)（`GPL-3.0-or-later`） |
| 28 | my.wei 中的服务器网段暂时公开；之后寻找既不公开、又能参与生成规则的办法 | 🕓 | 待设计 |
| 29 | 创建 GitHub 仓库；描述、主题等每一项元数据都认真填写，并先经维护者确认 | ✅ | [angwz/domainrouter_v2](https://github.com/angwz/domainrouter_v2) |
| 30 | 版本号体现「第二代」：以 2 开头，首个公开版本为 2.0.0 | ✅ | `pyproject.toml`、[CHANGELOG](../../CHANGELOG.md) |
| 31 | 许可证确定为 `GPL-3.0-or-later`；保留提交中的 Claude 共同作者署名；试运行通过后创建正式版本 v2.0.0 | ✅ | [v2.0.0](https://github.com/angwz/domainrouter_v2/releases/tag/v2.0.0) |
| 32 | 打开每日发布 | ✅ | `PUBLISH_ENABLED=true` |
| 33 | 尽量不在 GitHub 上制造杂物：由代理决定 Dependabot、版本附件与 v1 仓库的处理方式 | ✅ | Dependabot 只保留提醒；Release 不附加构件；v1 待切换订阅后归档 |
| 34 | 仓库主要自用：他人可以查看与提意见，但个性化规则不进入本仓库的发布；需要自用版本请 fork | ✅ | [CONTRIBUTING](../../CONTRIBUTING.md#这是一个自用仓库)、PR 仅限协作者 |
| 35 | v1 仓库保持原样，不归档、不改动 | ✅ | — |
| 36 | 发布的规则允许任何人自取；为访客提供取用地址与用法的简单指引 | ✅ | release 分支 README（自动生成）、主页「直接取用规则」 |
| 37 | 每日更新改为北京时间 06:00 | ✅ | [每日自动更新 · 时间](../guide/daily-automation.md#时间) |
| 38 | 访客的用法各不相同：只挑部分规则集、把这里当作上游收集、节点地区较少；取用指引应照顾这些情形，措辞更得体 | ✅ | release 分支 README（三种取用方式） |
| 39 | 实现 MRS 发布 | ✅ | [0003](../decisions/0003-publish-mrs.md) |
