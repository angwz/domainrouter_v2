# 接入 subconverter

产物针对 [angwz/subconverter](https://github.com/angwz/subconverter)（提交 `a33d49e`）的原生 provider 生成路径设计，与 v1 的接入方式相同：引用 `rulesets.toml` 和 `groups.toml`。

## 生成的内容

```toml
[[rulesets]]
group = "🌠 节点选择"
ruleset = "https://raw.githubusercontent.com/<owner>/domainrouter_v2/release/clash-domain/Proxy.yaml"
type = "clash-domain"
interval = 21600

[[rulesets]]
group = "DIRECT"
ruleset = "[]GEOIP,CN"

[[rulesets]]
group = "🐳 漏网の鱼"
ruleset = "[]MATCH"
```

- 每个合集最多三条：`clash-domain`、`clash-ipcidr`、`clash-classic`，按此顺序连续排列；没有内容的类别不生成。
- 规则集清单有两个版本，条目、顺序与指向的策略组完全相同，共用同一份 `groups.toml`：

  | 版本 | 文件 | 引用的规则文件 |
  | --- | --- | --- |
  | YAML | `rulesets.toml` | 全部为 YAML |
  | MRS | `rulesets-mrs.toml` | domain、ipcidr 为同名 `.mrs`，classical 为 YAML（classical 没有 MRS 形式） |

  `rulesets-mrs.toml` 在开启 `output.mrs` 时生成（[决定 0003](../decisions/0003-publish-mrs.md)）。使用它要求 subconverter 为 `.mrs` 引用写出 `format: mrs`：Mihomo 不按扩展名判断格式，没有 `format` 时一律按 YAML 读取。本文其余关于 fork 行为的说明对两个版本同样适用。
- `groups.toml` 校验通过后原样输出。

## subconverter 端需要满足的条件

以下结论来自 fork 源码，尚未在实际部署的 subconverter 上运行验证：

- 要走原生 provider 路径，`managed_config_prefix` 不能为空，且请求不能带 `expand=true`；还需开启 `enable_rule_generator`。
- 通过订阅链接 `config=` 加载外部配置时，fork 最多接受 **64** 条 rulesets，超出时构建会给出 `W_RULESET_LIMIT` 提示。在 pref 配置中直接导入 `rulesets.toml` 不受这个限制。
- fork 会给 `clash-ipcidr` 的引用自动追加 `,no-resolve`。
- 同名 provider 会被自动改名为 `名称_2`。本项目生成的文件名保证全局唯一（大小写不敏感），只有同一合集被重复引用时才会出现 `_2`，此时指向的是同一个文件。
- 内联规则 `[]X` 会变成 `X,组`；含三个及以上逗号时，fork 会用正则把组名移到参数前。因此值中含逗号的规则不能内联，构建时会报错。

## 验证方式

`domainrouter_v2 verify --level kernel` 会按上述规则模拟 fork 生成的 `rules` 与 `rule-providers`，交给 Mihomo v1.19.33 的真实规则引擎求值，见[架构与验证](../design/architecture.md#验证)。
