# DomainRouter v2

把个人分流配置 `my.wei` 和各处收集的上游规则，编译成去重、合并、按 Mihomo 匹配机制优化过的 rule-provider，以及 subconverter 直接可用的 `rulesets.toml`、`groups.toml`。由 GitHub Actions 每天自动刷新上游并发布。

> 状态：开发中（0.1.0.dev0）。核心构建、验证与每日流程已在本地实现并演练；远端仓库、实际发布与开源许可尚未启用，见[进度](docs/development/progress.md)。

## 它做什么

```text
my.wei + groups.toml ──┐
                       ├─▶ 解析 ─▶ 规范化 ─▶ 等价优化 ─▶ 规划 ─▶ clash-domain/*.yaml
上游规则（每天刷新）────┘                                      clash-ipcidr/*.yaml
                                                                clash-classic/*.yaml
                                                                rulesets.toml · groups.toml
```

- **读懂多种来源格式**：Mihomo、Surge、Loon、sing-box、AdGuard DNS、hosts、dnsmasq，全部按各自官方文档的语义转换；只保留匹配条件，上游自带的策略（`DIRECT`、`REJECT` 等）和附加参数一律剥离。
- **精确去重与合并**：域名按完整标签判断包含关系（含 `*` 通配），IP 网段按区间精确合并，结果既不扩大也不缩小匹配范围。
- **为匹配效率规划输出**：能放进 domain/ipcidr 集合的条件都放进集合（内核中为 O(1)/O(log n) 查找），classical 只保留集合表达不了的条件并按成本排序；相邻且目标相同的合集合并成一组文件，减少 RULE-SET 条数。
- **拦住过宽的上游规则**：`DOMAIN-KEYWORD,ads`、`0.0.0.0/0`、`NETWORK,UDP` 这类接近“全部流量”的上游条目会被过滤；关键词、GEOIP、整个公共后缀等宽泛规则逐条列入清单供你检查（[判定规则](docs/rules/broad-rules.md)）。
- **不擅自改你的意图**：手写规则按原样保留，`[Rules]` 顺序就是匹配优先级。
- **每天自动更新**：上游变化就重新生成；内容没变不提交；某个上游失败时沿用它上次成功的内容，并在更新说明里提醒。
- **有证据的验证**：独立参考实现对照优化前后的匹配结果，再用固定版本 Mihomo 的真实规则引擎复核。

## 快速开始

需要 [uv](https://docs.astral.sh/uv/)（会自动准备 Python 3.13）。

```sh
git clone https://github.com/angwz/domainrouter_v2.git
cd domainrouter_v2
uv sync --locked

# 离线运行公共最小示例
cd examples/minimal
uv run --locked domainrouter_v2 check
uv run --locked domainrouter_v2 build
uv run --locked domainrouter_v2 explain --host video.cdn.example.org
```

`build` 在 `examples/minimal/dist/` 生成：

```text
clash-domain/Streaming.yaml      clash-domain/Work.yaml
clash-ipcidr/Streaming-ipcidr.yaml  clash-ipcidr/Work-ipcidr.yaml
clash-classic/Streaming-classic.yaml  clash-classic/Work-classic.yaml
rulesets.toml  groups.toml  manifest.json  reports/broad-rules.md
```

规则文件开头是简短的 `# NAME:`、`# GROUP:`、`# TYPE:`、`# TOTAL:` 等注释；发布时加上 `# UPDATED:`，只在该文件内容变化时更新。domain 条目按覆盖范围从宽到窄排列（`+.` 一级 → 二级 → … → 精确主机名），见[排列与文件头](docs/rules/merge-cases.md#10-规则文件的排列与文件头)。

使用自己的配置时，编辑仓库根目录的 `my.wei`、`subconverter_config/groups.toml` 和 `config/domainrouter_v2.toml`，然后：

```sh
uv run --locked domainrouter_v2 fetch    # 联网获取上游，更新本地快照
uv run --locked domainrouter_v2 build    # 只用快照构建，不联网
uv run --locked domainrouter_v2 verify   # 语义层验证；--level kernel 另用真实 Mihomo 复核
```

## 一个例子

```text
[Streaming]
example.com                    # 自身及全部子域 → +.example.com
'api.example.net'              # 单引号：仅自身 → api.example.net
*.cdn.example.org              # 一级通配加子域闭包 → .cdn.example.org
192.0.2.0/25
192.0.2.128/25                 # 与上一行精确合并为 192.0.2.0/24
https://example.org/list.txt   # 上游来源，格式自动识别

[Rules]
Streaming: 🎬 Media
GEOIP,CN: DIRECT
MATCH: 🐟 Final
```

完整语法见 [my.wei 语法](docs/my-wei.md)，每种来源格式的转换规则见[转换与合并案例](docs/rules/merge-cases.md)。

## 文档

| 主题 | 文档 |
| --- | --- |
| my.wei 语法与语义 | [docs/my-wei.md](docs/my-wei.md) |
| 来源格式、去重合并的全部案例 | [docs/rules/merge-cases.md](docs/rules/merge-cases.md) |
| 宽泛规则的过滤与提醒 | [docs/rules/broad-rules.md](docs/rules/broad-rules.md) |
| 配置文件 | [docs/configuration.md](docs/configuration.md) |
| 接入 subconverter | [docs/subconverter.md](docs/subconverter.md) |
| 每日自动更新、启用与回滚 | [docs/daily-automation.md](docs/daily-automation.md) |
| 架构与验证方式 | [docs/architecture.md](docs/architecture.md) |
| 性能数据 | [docs/performance.md](docs/performance.md) |
| 从 v1 迁移 | [docs/migration/v1-report.md](docs/migration/v1-report.md) |
| 设计决定 | [docs/decisions/](docs/decisions/) |
| 参与开发 | [CONTRIBUTING.md](CONTRIBUTING.md) |

## 支持范围

| 项目 | 状态 |
| --- | --- |
| 输出 | Mihomo rule-provider（YAML）+ subconverter TOML |
| 验证目标 | Mihomo v1.19.33；subconverter 行为按 angwz/subconverter@a33d49e 源码模拟 |
| 平台 | Windows 10 x64 已实测；Linux 由 CI 覆盖（远端启用后生效） |
| 计划中 | MRS 二进制输出（需 subconverter 支持写出 `format`）、Web 编辑界面、AI 建议 |
| 不支持 | Quantumult X、Shadowrocket 等无正式语法文档的格式；二进制规则输入（`.mrs`、`.srs`、`.dat`） |

## 许可

尚未选定开源许可证，首次公开发布前确定。在此之前，本仓库的代码不授予任何许可。第三方工具与数据的来源和许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
