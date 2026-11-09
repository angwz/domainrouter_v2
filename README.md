# DomainRouter v2

把一份手写的分流配置 `my.wei` 与各处收集的上游规则，编译成去重、合并、按 Mihomo 匹配机制优化的 rule-provider，以及 subconverter 直接可用的 `rulesets.toml`、`groups.toml`。GitHub Actions 每天刷新上游、验证并发布。

> **状态** 2.0.0 · 首个公开版本；进度见 [progress](docs/development/progress.md)。

```text
my.wei · groups.toml ─┐
                      ├─▶ 解析 ─▶ 过滤 ─▶ 等价优化 ─▶ 规划 ─▶ clash-domain/   *.yaml
上游规则（每日刷新）──┘                                       clash-ipcidr/   *.yaml
                                                              clash-classic/  *.yaml
                                                              rulesets.toml · groups.toml
```

## 特点

- **按官方文档读懂上游。** Mihomo、Surge、Loon、sing-box、AdGuard DNS、hosts、dnsmasq，各按自身语义转换；只保留匹配条件，上游自带的策略与参数一律剥离。
- **精确的去重与合并。** 域名按完整标签判断包含（含 `*` 通配），网段按区间合并；匹配范围不扩大、不缩小，并由真实 Mihomo 复核。
- **为匹配效率规划。** 能进 domain/ipcidr 集合的条件都进集合，查找成本与条目数无关；classical 只留集合表达不了的条件，按成本排序；目标相同的相邻合集共用一组文件。
- **拦住过宽的规则。** `DOMAIN-KEYWORD,ads`、`0.0.0.0/0`、`NETWORK,UDP` 这类接近全部流量的上游条目被过滤，其余宽泛规则逐条列入清单（[判定依据](docs/rules/broad-rules.md)）。
- **每条规则都有来历。** 同行注释标出它来自哪些上游、合并或覆盖了哪些规则；`explain --rule` 列出完整清单。
- **尊重手写意图。** `my.wei` 中手写的内容按原样保留，`[Rules]` 的顺序就是匹配优先级。
- **稳定的每日更新。** 内容没变就不提交；单个上游失败时沿用其上次成功的副本，并在更新说明中提醒。

## 产物一瞥

```yaml
# NAME: America
# GROUP: ⛳ 美国专线
# REPO: https://github.com/angwz/domainrouter_v2
# UPDATED: 2026-11-10 06:08:31 (UTC+8)
# TYPE: domain
# TOTAL: 1683
# SOURCE A: my.wei
# SOURCE B: blackmatrix7 · USMedia/USMedia.list
# SOURCE C: MetaCubeX · geosite/category-dev.yaml
payload:
  - '+.us'                     # A  覆盖 +.hulu.us B, +.intel.us I J 等 3 条
  - '+.01.org'                 # C I J
  - '+.adobe.com'              # E F  覆盖 +.advertising.adobe.com E, 3dns-1.adobe.com E 等 132 条
  - 'vscode.blob.core.windows.net'  # C
```

domain 条目按覆盖范围从宽到窄排列：`+.` 一级、二级……，再到通配与精确主机名。字段与注释格式见[排列与来源标注](docs/rules/merge-cases.md#10-规则文件的排列与文件头)。

在维护者的真实配置上（210 个上游来源），规则条目从 63.8 万条降到 20.1 万条，Mihomo 加载全部规则从约 8.5 s 降到 3.3 s，优化前后 5 万个请求的命中结果完全一致（[性能](docs/design/performance.md)）。

## 直接取用规则

不想自己构建，可以直接引用每天发布的规则文件。规则一览、下载地址，以及 Mihomo、subconverter 的写法，都在 [`release` 分支的说明页](https://github.com/angwz/domainrouter_v2/tree/release#readme)，随每次发布自动更新。

## 快速开始

需要 [uv](https://docs.astral.sh/uv/)，它会自动准备 Python 3.13。

```sh
git clone https://github.com/angwz/domainrouter_v2.git
cd domainrouter_v2
uv sync --locked

cd examples/minimal                                  # 离线的最小示例
uv run --locked domainrouter_v2 build
uv run --locked domainrouter_v2 explain --host video.cdn.example.org
uv run --locked domainrouter_v2 explain --rule '192.0.2.0/24'
```

使用自己的配置时，编辑仓库根目录的 `my.wei`、`subconverter_config/groups.toml` 与 `config/domainrouter_v2.toml`：

```sh
uv run --locked domainrouter_v2 fetch     # 联网获取上游，更新本地快照
uv run --locked domainrouter_v2 build     # 只用快照构建，不联网
uv run --locked domainrouter_v2 verify    # 语义层验证；--level kernel 另用真实 Mihomo 复核
```

## my.wei 一瞥

```text
[Streaming]
example.com                    # 自身及全部子域 → +.example.com
'api.example.net'              # 单引号：仅自身 → api.example.net
*.cdn.example.org              # 一级通配及其下级 → .cdn.example.org
192.0.2.0/25
192.0.2.128/25                 # 与上一行合并为 192.0.2.0/24
https://example.org/list.txt   # 上游来源，格式自动识别

[Rules]
Streaming: 🎬 Media
GEOIP,CN: DIRECT
MATCH: 🐟 Final
```

完整语法见 [my.wei 语法](docs/guide/my-wei.md)。全部文档从[文档地图](docs/README.md)进入。

## 支持范围

| 项目 | 状态 |
| --- | --- |
| 输出 | Mihomo rule-provider（YAML）与 subconverter TOML |
| 验证目标 | Mihomo v1.19.33；subconverter 行为按 angwz/subconverter@a33d49e 源码模拟 |
| 平台 | Windows 10 x64 已实测；Linux 由 CI 覆盖 |
| 计划中 | MRS 输出、Web 编辑界面、AI 建议 |
| 不支持 | Quantumult X、Shadowrocket 等没有正式语法文档的格式；二进制规则输入（`.mrs`、`.srs`、`.dat`） |

## 参与与许可

这是维护者的自用仓库：欢迎通过 Issue 提意见；想要自己的规则，请 fork 后修改 `my.wei`，副本不会影响这里的发布（[详情](CONTRIBUTING.md#这是一个自用仓库)）。开发约定见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题见 [SECURITY.md](SECURITY.md)。

以 [GNU GPL v3.0 或更新版本](LICENSE) 发布（`GPL-3.0-or-later`）。第三方工具与数据的来源和许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
