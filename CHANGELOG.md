# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。规则产物的每日变化不在这里记录，见 `release` 分支的 `reports/latest.md`。

## [未发布]

### 新增

- MRS：`output.mrs` 开启后，为 domain、ipcidr 文件同时发布同名 `.mrs`；内核层验证增加 MRS 变体，对照 YAML 的命中结果与条目数。
- release 分支自动生成 README：规则一览、下载地址（含 jsDelivr），以及 Mihomo、作为上游、subconverter 三种取用方式。

### 变更

- 每日更新改为北京时间 06:00；release 与 state 的提交信息使用北京时间日期。

## [2.0.0] - 2026-11-09

首个公开版本。

### 新增

- `my.wei` 解析：手写域名默认包含子域、单引号仅自身、原生通配、显式规则、`@source`/`@site` 指令、粘贴块、`[Rules]`。
- 来源格式：Mihomo（domain/ipcidr/classical，yaml 与 text）、Surge 规则列表与 DOMAIN-SET、Loon、sing-box source、AdGuard DNS、hosts、dnsmasq、完整 Clash 配置；按内容自动识别。
- 等价优化：域名精确包含判定与合并、网段精确合并、classical 去重与成本排序、端口合并、相邻同目标合集合并。
- 输出：Mihomo rule-provider YAML、`rulesets.toml`、`groups.toml`、确定性 `manifest.json`。
- 来源快照与健康检查；上游失败时沿用上次成功的内容。
- 命令：`check`、`fetch`、`build`、`publish`、`verify`（语义层/内核层）、`explain`、`tools prepare`。
- 每日 GitHub Actions 工作流与本地演练脚本。
- 宽泛规则：过滤上游中过宽的规则（通用词关键词、`0.0.0.0/0`、`NETWORK`、含 80/443 的 `DST-PORT` 等），并把所有宽泛规则列入随发布的 `reports/broad-rules.md`；手写规则只提醒。
- 规则文件头注释（NAME、GROUP、REPO、UPDATED、TYPE、TOTAL），UPDATED 只在文件内容变化时更新。
- 来源标注：规则文件头的来源图例，每条规则的同行注释（来源、合并、覆盖）；`explain --rule` 查看完整来历；仅标注变化时也会发布。
- domain 文件按覆盖范围从宽到窄排列（`+.` 按层级 → `.` → `*` 通配 → 精确主机名），classical 类型之间空行。

[未发布]: https://github.com/angwz/domainrouter_v2/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/angwz/domainrouter_v2/releases/tag/v2.0.0
