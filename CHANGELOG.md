# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。规则产物的每日变化不在这里记录，见 `release` 分支的 `reports/latest.md`。

## [未发布]

### 新增

- `my.wei` 解析：手写域名默认包含子域、单引号仅自身、原生通配、显式规则、`@source`/`@site` 指令、粘贴块、`[Rules]`。
- 来源格式：Mihomo（domain/ipcidr/classical，yaml 与 text）、Surge 规则列表与 DOMAIN-SET、Loon、sing-box source、AdGuard DNS、hosts、dnsmasq、完整 Clash 配置；按内容自动识别。
- 等价优化：域名精确包含判定与合并、网段精确合并、classical 去重与成本排序、端口合并、相邻同目标合集合并。
- 输出：Mihomo rule-provider YAML、`rulesets.toml`、`groups.toml`、确定性 `manifest.json`。
- 来源快照与健康检查；上游失败时沿用上次成功的内容。
- 命令：`check`、`fetch`、`build`、`publish`、`verify`（语义层/内核层）、`explain`、`tools prepare`。
- 每日 GitHub Actions 工作流与本地演练脚本。
