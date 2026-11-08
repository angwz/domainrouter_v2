# my.wei 语法

`my.wei` 是唯一需要手写的规则文件：用「合集」组织规则，用 `[Rules]` 决定匹配顺序和去向。构建只读取它，从不改写。

```text
[合集名]
规则、上游来源、粘贴块……

[Rules]
合集名: 策略组
内联规则: 策略组[,参数]
MATCH: 策略组
```

## 节

- 节标题必须从行首开始：`[名称]`，后面只能有空白或注释。规则或正则里的方括号不会被当成节。
- 合集名区分大小写；同名合集重复出现时按顺序合并，并给出提示。
- `[Rules]` 是保留名，只能出现一次。
- 以 `#`、`;`、`//` 开头的行是注释。

## 合集中的一行

识别顺序：显式规则 → 地址/网段 → 域名。

### 域名

手写域名默认包含全部子域；单引号取消这一扩展。

| 写法 | 含义 | 输出 |
| --- | --- | --- |
| `a.hk` | 自身及全部子域 | `+.a.hk` |
| `'a.hk'` | 仅自身 | `a.hk` |
| `"a.hk"` | 双引号只是容器，同裸写 | `+.a.hk` |
| `'*.a.hk'` | 恰好一级子域 | `*.a.hk` |
| `*.a.hk` | 一级子域及其全部下级（不含自身） | `.a.hk` |
| `.a.hk`、`'.a.hk'` | 全部子域，不含自身 | `.a.hk` |
| `+.a.hk`、`'+.a.hk'` | 自身及全部子域 | `+.a.hk` |
| `'xbox.*.example.com'` | 中间一个完整标签 | `xbox.*.example.com` |
| `xbox.*.example.com` | 上一模式及全部下级 | `+.xbox.*.example.com` |

- `*` 只能代表一个完整标签。`foo*.example.com` 这类局部通配会报错，请改用 `DOMAIN-WILDCARD,foo*.example.com`。
- 单独一行的 `*`、`+`、`.` 含义不明确，会报错；确实需要全通配时写成单引号的 `'*'` 或 `'+.*'`。
- 大小写、末尾的根点会自动修复；中文等国际化域名会转换为 `xn--` 形式。修复都会记录在构建诊断里。
- 列表符号（`- `、`* `）、成对的中文引号、Markdown 反引号会被去掉，不改变上面的语义。

### 地址与网段

`192.0.2.1` 视为 `/32`，IPv6 单地址视为 `/128`。带主机位的网段会按掩码规范化并提示。合集中的目标地址都放进 ipcidr 文件，subconverter 引用时会加 `no-resolve`。

### 显式规则

`DOMAIN,a.hk`、`DOMAIN-SUFFIX,a.hk`、`DOMAIN-KEYWORD,x`、`GEOIP,CN`、`DST-PORT,9993` 等按 Mihomo 规则类型解释。

- `DOMAIN`、`DOMAIN-SUFFIX` 的值是字面域名，不接受 `*`、`+` 或前导点。
- 合集中的目标 IP 条件（`GEOIP`、`IP-ASN`、`IP-SUFFIX`）会加上 `no-resolve`。
- 末尾的策略字段会被忽略：去向只由 `[Rules]` 决定。

### 上游来源

```text
https://example.org/rules.list                         # 格式自动识别
@source https://example.org/domains.txt format=surge-domainset
@source https://example.org/config.yaml format=clash-config exclude_types=MATCH,FINAL
@site https://www.example.com/some/page                # 只取主机名，按域名后缀处理
```

可用格式：`auto`、`mihomo`、`domain`、`ipcidr`、`classical`、`surge`、`surge-domainset`、`loon`、`singbox`、`adguard`、`hosts`、`dnsmasq`、`clash-config`、`wei`。每种格式的语义和边界情况见[转换与合并案例](rules/merge-cases.md)。

自动识别遇到有歧义的内容时会报错，并要求写明 `format=`。最常见的情况是列表以 `.` 开头：Surge DOMAIN-SET 中 `.x` 包含 x 本身，Mihomo 中不包含。

### 粘贴块

直接粘贴别处的规则时，用显式块划定边界：

```text
@begin format=domain
payload:
  - '*.a.hk'
@end
```

块内内容完全交给指定格式解析（这里的单引号只是 YAML 容器，`'*.a.hk'` 仍是恰好一级子域）。行首的 `payload:` 或 `rules:` 也会开启一个隐式块，吸收其后缩进的条目，遇到回到行首的内容行时结束。

## [Rules]

每行是「条件: 目标」，冒号后需要空白。顺序就是最终的匹配优先级。

```text
[Rules]
Direct: DIRECT
AI: 🗨️ ChatGPT
GEOIP,JP: 🌺 日本专线,no-resolve
GEOIP,CN: DIRECT
MATCH: 🐳 漏网の鱼
```

- **合集引用**：`合集名: 策略组`，不接受附加参数。同一合集可以引用多次。
- **内联规则**：`类型,值: 策略组[,no-resolve|src]`，参数按你写的原样保留。值中含逗号的规则（`DOMAIN-REGEX`、`AND`/`OR`/`NOT`）不能内联：subconverter 会重排含逗号的内联规则导致损坏，请放进合集。
- **MATCH**（或 `FINAL`）必须有且只有一条，并且位于最后。
- 目标必须是 `groups.toml` 中的组，或内置的 `DIRECT`、`REJECT` 等。
- 相邻且目标相同的合集引用会合并成一组文件，命中结果不变（见[决定 0001](decisions/0001-deviations-from-spec-1.5.md)）。
- 没有被 `[Rules]` 引用的合集不生成文件，构建时给出提示。被引用但最终没有任何规则的合集会报错，除非在配置的 `policy.allow_empty_collections` 中允许。
