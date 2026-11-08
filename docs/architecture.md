# 架构与验证

## 管线

```text
fetch（联网）                     build（不联网）
───────────────                  ─────────────────────────────────────────────────────────
上游 URL ─▶ 下载 ─▶ 健康检查 ─▶ 快照   my.wei ─▶ 解析 ─┐
                                 快照 ─────────────────┼─▶ 合集成员 ─▶ 宽泛规则过滤 ─▶ 规划与优化 ─▶ 输出
                                 groups.toml ─▶ 校验 ──┘
```

- **fetch** 是唯一联网的步骤：并发下载、健康检查、解析并规范化，成功后把来源的成员写成快照。失败时保留上次成功的快照。
- **build** 只读快照与输入文件，结果确定：同样的输入两次构建逐字节相同。出现任何错误都不写出，已有的输出目录保持不变。汇总合集成员时，过滤上游中范围过宽的规则（[broad-rules](rules/broad-rules.md)）。
- **publish** = build + 与上次发布比较 + 生成更新说明 + 暂存到 release 目录；内容没变时什么也不写。

## 模块

| 模块 | 职责 |
| --- | --- |
| `model/` | 域名模式（含包含判定）、网段与区间合并、规则条件树、解析后的 profile |
| `registry.py` | 规则类型注册表：分区、成本次序、是否目标 IP 条件、同义名 |
| `parse/` | `my.wei` 文档与自由行、规则行转换（剥离策略与参数）、安全 YAML、各来源格式适配器与自动识别 |
| `sources/` | 下载（含 Happy Eyeballs 连接竞速）、健康检查、快照与健康记录 |
| `breadth.py`、`data/` | 宽泛规则判定（关键词表、Public Suffix List）、上游过宽规则过滤、`reports/broad-rules.md` |
| `optimize/` | domain 集合去重与包含消除、classical 去重与成本排序 |
| `planner.py` | 路由块（相邻同目标合并）、分区、文件命名与碰撞处理、rulesets 条目 |
| `emit.py` | provider YAML（文件头、展示次序）、TOML、确定性 manifest；发布时写入的 `UPDATED` |
| `build.py` | 构建编排与原子写出 |
| `report.py`、`publish.py` | 更新说明与 release 暂存 |
| `explain.py` | 命中解释 |
| `verify/` | 参考解释器、语义层与内核层验证 |
| `tools.py` | 验证工具的锁定、下载与校验 |
| `cli.py` | 命令行 |

依赖方向：`cli` → `build`/`report`/`publish`/`verify` → `planner`/`optimize`/`parse`/`sources`/`breadth` → `model`/`registry`/`diagnostics`。`model` 不依赖其他模块；只有 `sources` 和 `tools` 访问网络。

## 关键算法

**域名包含**（`model/domain.py`）：每个原生模式表示为「标签数区间 + 从右数的固定标签表」。P 被 Q 包含，当且仅当 P 的长度区间落在 Q 的区间内，并且 Q 的每个固定标签在 P 的同一位置也是同一个标签。判定是精确的，单对成本与固定标签数成正比。实现用小字母表穷举（全部模式对）与属性测试交叉校验。

**domain 集合优化**（`optimize/domain.py`）：按「从右往左的固定标签」建 trie，找覆盖者时只沿相同标签或 `*` 分支下行。这样候选是完备的，常规输入下总成本与标签总数成正比。合并（如 `a.com` + `.a.com` → `+.a.com`）与包含消除交替进行，直到不再变化。

**网段合并**（`model/ip.py`）：把网段转为整数区间，排序后合并重叠和相邻区间，再分解为最少的对齐 CIDR。复杂度 O(n log n)，不枚举地址。

**classical**（`optimize/classical.py`）：一个 classical provider 只回答「是否命中」，成员之间是并集。所有目标 IP 条件都带 `no-resolve`，剩下唯一的副作用是进程查询，且每次连接最多查询一次。因此可以安全地去重与重排：便宜的条件在前，进程类在最后。关键字 k2 包含另一个关键字 k1 时，k2 冗余，删除。同类端口条件合并为一条。逻辑表达式内部不改写。

## 验证

| 层 | 命令 | 做什么 | 依据 |
| --- | --- | --- | --- |
| 单元与属性测试 | `pytest` | 语义表、全部合并案例、边界；随机输入下语言不变、无残留包含、幂等 | [merge-cases](rules/merge-cases.md) |
| 语义层 | `verify --level semantic` | 用独立参考实现（哈希查表 + 逐条通配；整数区间二分）在由输入派生的边界探测点上，对照每组规则优化前后的结果 | `verify/semantic.py` |
| 内核层 | `verify --level kernel` | 模拟 subconverter 生成订阅，用 Mihomo v1.19.33 的真实配置解析、provider 加载与 `Rule.Match`，对照未优化与优化后两套 provider 的命中规则、目标和 DNS 解析请求；并核对每个 provider 加载的条目数与文件一致 | `verify/kernel.py`、`tools/kernel-adapter/` |

内核层需要先运行 `domainrouter_v2 tools prepare`，按 `src/domainrouter_v2/tools.lock.json` 下载并校验 Mihomo、Go 与地理数据。验证只调用已准备好的工具，不会隐式下载。

## 设计取舍

- 构建不联网，上游内容只来自快照：这样每日流程中的验证和发布用的是同一份内容，失败也能定位到具体来源。
- 快照保存规范化后的成员，而不是上游原文：体积小、git 增量友好，也不在仓库中再分发第三方原始文件。
- 下载层实现了 Happy Eyeballs（RFC 8305）。在 IPv6 不通的网络里，标准库按顺序尝试地址，每个 IPv6 地址都要等到连接超时；实测会让一次完整刷新从 29 秒拖到 17 分钟。
