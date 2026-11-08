# 从 v1 迁移

## 来源

- 仓库：`https://github.com/angwz/DomainRouter`，固定提交 `5bcb86f540883712726d37129c5ff493585be6bb`。
- 只读获取了以下文件，副本与 SHA-256 记录在本地 `.cache/migration-v1/SOURCE.txt`（不提交）：

| 文件 | SHA-256 |
| --- | --- |
| `my.wei` | `78b0c5841ac9afea58c6a6183c41b8697b11236719e2c90b463c65597ddada01` |
| `subconverter_config/groups.toml` | `34d2dc869ff241d2c77e5c352e95fd386c866d685bee324d3fa6611473f76fe2` |
| `README.md`、`script/domain_router.py`、`script/generate_rulesets.py`、两个工作流 | 仅作参考，未运行 |

- 根目录的 `my.wei` 与 `subconverter_config/groups.toml` 是上述文件的逐字节副本，作为 v2 的初始输入。之后每天只刷新其中引用的上游，不再从 v1 覆盖。

## 预览结果（2026-11-08）

| 项目 | 结果 |
| --- | --- |
| `check` | 0 错误，0 警告：21 个合集、28 条路由、210 个去重后的上游来源 |
| `fetch` | 210 个来源全部成功，0 条未转换；格式自动识别为 Mihomo YAML 101 个、Surge 规则列表 107 个、Mihomo 域名文本 2 个 |
| `build` | 59 个规则文件、`rulesets.toml` 66 条、`groups.toml` 校验通过 |
| `verify --level kernel` | 语义层与内核层均 0 不一致 |

每个合集的去重、覆盖与合并统计见构建生成的 `reports/latest.md`。

## 需要你知道或决定的事

1. **v1 的 `release` 分支**曾在 2026-11-08 被清空（提交 `0addd6f`），用户已重新运行 v1 工作流恢复。
2. **`rulesets.toml` 有 66 条**，超过 subconverter 外部配置（订阅链接 `config=`）的 64 条上限。用户确认不影响其使用方式；构建仍会给出 `W_RULESET_LIMIT` 提示。
3. **宽泛规则**：当前上游中没有被过滤的条目，但有 177 条 DOMAIN-KEYWORD 等宽泛规则被列入 `reports/broad-rules.md`。其中一部分出现在意外的合集里，例如 `China`（DIRECT）中的 `DOMAIN-KEYWORD,microsoft`，`AI` 中的 `DOMAIN-KEYWORD,twitter`。判定规则见 [broad-rules](../rules/broad-rules.md)。
4. **`GEOIP,CLOUDFLARE`** 依赖客户端使用的 GeoIP 数据库中存在 `CLOUDFLARE` 分类。已实测：固定版本的 MetaCubeX `geoip.metadb` 中，1.1.1.1 命中 `GEOIP,CLOUDFLARE`；其他 GeoIP 数据库可能没有这个分类。
5. **MetaCubeX geosite 的 domain 版 YAML** 在转换时去掉了 `keyword` 与 `regexp` 条目，例如 `geolocation-!cn.yaml`。如果需要这些条目，可以改用其 `classical/` 目录下的同名文件。这只是建议，当前输入不做改动。
6. **`GEOIP,CN: DIRECT` 不带 `no-resolve`**：按你的说明原样保留。它是唯一会在匹配阶段请求 DNS 解析的规则，每次构建的报告都会列出这一点。

## 与 v1 行为的差异

| 方面 | v1 | v2 |
| --- | --- | --- |
| 上游策略字段 | IP 规则会剥离，classical 中的策略（如 `REJECT`）原样保留 | 一律剥离，只保留匹配条件 |
| 上游 IP 条件 | classical 中名称含 "ip" 的类型追加 `no-resolve` | 按类型注册表判断，目标 IP 条件统一加 `no-resolve`；`src` 参数转换为 `SRC-*` 类型 |
| 域名合法性 | 顶级域不超过 6 个字母等过时校验，会误删合法域名 | 按标签校验；不按 DNS 是否存在判断 |
| 去重 | 字符串层面 | 按匹配语言精确判断包含，含通配 |
| 格式识别 | 按字符串猜测 | 按各格式官方语义；有歧义时要求指定 |
| 发布 | 强推 release、每次建 Release | 快进推送、内容不变不提交、失败保留上一版 |
| 生成 `rulesets.toml` | 逐个探测已发布 URL 是否 200 | 由本次构建的产物清单决定 |
| 宽泛规则 | 不处理 | 过滤上游中的过宽规则，宽泛规则列入 `reports/broad-rules.md` |
| 文件头注释 | NAME、AUTHOR、REPO、UPDATED、TYPE、TOTAL；每次运行所有文件的 UPDATED 都会变 | NAME、GROUP、REPO、UPDATED、TYPE、TOTAL；UPDATED 只在该文件内容变化时更新，未变化的文件保持原样 |

## 切换步骤

见[每日自动更新 · 启用步骤](../daily-automation.md#启用步骤m4b需要你操作)。v2 发布稳定后再停用 v1 的工作流，避免两套流程同时更新。
