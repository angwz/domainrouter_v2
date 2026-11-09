# 0001 · 相对实施规范 1.5 的调整

- 状态：已采纳（2026-11-08，维护者逐条确认）
- 范围：覆盖 [实施规范 1.5](../history/spec-1.5/index.md) 中与下列内容冲突的条款；未提及的条款仍然有效。

## 背景

规范 1.5 以 MRS 发布、generation 目录、完整 base 桥接和 subconverter fork 集成验证为核心交付。实施前的讨论与源码调研确认了用户的实际使用方式：VPS 上的 subconverter 只引用 `rulesets.toml`、`groups.toml` 和规则文件，而该 fork 不会为 provider 写出 `format` 字段。用户的首要目标是 Clash/Mihomo 的匹配效率，以及上游规则每天跟随更新。

## 决定

| # | 主题 | 决定 | 替代的规范条款 |
| --- | --- | --- | --- |
| 1 | 输出格式 | domain、ipcidr、classical 全部输出 YAML `payload:`；MRS 推迟（后由 [0003](0003-publish-mrs.md) 补充发布） | §2、§10.1、§11.2、M01–M08 |
| 2 | 配套配置 | 只生成 `rulesets.toml`、`groups.toml`；不生成 `clash-base.yaml`、`provider-overrides.yaml`、`external-config.toml` | §11.1、§12.1、§12.3 |
| 3 | 发布路径 | 固定路径：`release` 分支下的 `clash-domain/`、`clash-ipcidr/`、`clash-classic/`、两份 TOML、`reports/`；同一次提交更新 | §15.2 的 generation 目录 |
| 4 | 上游刷新 | 每天抓取最新内容；来源锁是当天的收据，用于判断有无变化和事后追溯，不冻结上游 | §6 的语义不变，用途说明 |
| 5 | 来源失败 | 改用该来源上次成功的规范化副本（存放在 `state` 分支），其余照常发布；连续失败超过 7 天时在更新说明顶部提示 | §6「默认任一必需来源失败则本次失败」 |
| 6 | 支持的格式 | 只支持有官方文档的格式：Mihomo、Surge、Loon、sing-box source、AdGuard DNS、hosts、dnsmasq；不支持 Quantumult X | §5 格式矩阵 |
| 7 | 上游字段 | 上游规则只保留匹配条件，策略字段与参数一律剥离；上游目标 IP 条件统一加 `no-resolve` | §5 |
| 8 | 手写内联规则 | `[Rules]` 中手写的内联规则按原样保留参数（例如有意不带 `no-resolve` 的 `GEOIP,CN`），报告中只标注会触发 DNS 的条目 | §8.2「首版对所有目标 IP 条件启用」 |
| 9 | 域名规范化 | 所有来源的 Unicode 域名统一转为 A-label，末尾根点去除，均记录在说明中 | §8.1「第三方保留字面或拒绝」 |
| 10 | 匹配效率 | 按内核实际数据结构优化：能进集合的进集合；classical 按成本排序；`[Rules]` 中相邻且目标相同的合集引用合并为一组文件 | §9.6、§10.3（补充） |
| 11 | 验证层级 | 语义层（独立参考解释器）与内核层（Go 薄适配器调用 Mihomo v1.19.33）；不做 fork 集成层 | §12、§13.1 第 3 层 |
| 12 | 范围外 | Web、AI、远端创建、实际发布、VPS 变更 | 同规范 |

## 取舍

- **YAML 而非 MRS**：MRS 只缩短加载时间，不改变匹配速度（两者在内核中是同一数据结构）；而该 fork 不写 `format`，用 MRS 需要改 base 或改服务。以后 subconverter 支持透传 `format` 时再启用。
- **固定路径而非 generation 目录**：上游几乎每天变化，按 generation 保存会让发布分支持续膨胀；用户的订阅只用一套最新入口。代价是客户端刷新间隙可能短暂看到新旧文件混用，通过同一提交更新、文件名稳定来降低影响。
- **失败时用旧副本**：任一上游不稳定都不应拖住全部分组的每日更新；代价是该来源的内容可能滞后，因此在说明中持续告警。
- **相邻同目标合并**：连续指向同一策略组的规则，取并集后命中结果相同，且 domain 集合先于 classical 求值，触发 DNS/进程查询的机会只会减少；合并只发生在相邻引用之间。

## 验证方式

- [docs/rules/merge-cases.md](../rules/merge-cases.md) 中每个案例都有对应测试。
- 内核层测试用真实 Mihomo provider 求值，对比未优化与优化后的匹配结果。
