# DomainRouter v2 · 规则发布

这里是 [DomainRouter v2](https://github.com/angwz/domainrouter_v2) 每天自动生成的规则。它们首先服务于维护者自己的分流配置，也欢迎任何人取用：整套照搬、只挑几个规则集，或者像维护者收集上游一样，把这里当作你的上游之一。

- **更新**：每天北京时间 06:00 前后，内容没有变化时不产生新提交。
- **来源**：规则数据来自各上游规则集，经去重合并后发布，适用上游原有的条款。
- **来历**：YAML 文件开头列出来源，每条规则的同行注释标出它来自哪个上游。
- **说明**：本次变化见 [reports/latest.md](reports/latest.md)，范围较大的规则见 [reports/broad-rules.md](reports/broad-rules.md)。

## 规则一览

| 规则集 | behavior | 条目 | 维护者的用法 | 下载 |
| --- | --- | ---: | --- | --- |
| Direct | `domain` | 1,980 | DIRECT | [YAML](clash-domain/Direct.yaml) · [MRS](clash-domain/Direct.mrs) |
| Direct | `ipcidr` | 530 | DIRECT | [YAML](clash-ipcidr/Direct-ipcidr.yaml) · [MRS](clash-ipcidr/Direct-ipcidr.mrs) |
| Direct | `classical` | 53 | DIRECT | [YAML](clash-classic/Direct-classic.yaml) |
| NS | `domain` | 7 | 🏖️ Community | [YAML](clash-domain/NS.yaml) · [MRS](clash-domain/NS.mrs) |
| NS | `classical` | 1 | 🏖️ Community | [YAML](clash-classic/NS-classic.yaml) |
| AI | `domain` | 304 | 🗨️ ChatGPT | [YAML](clash-domain/AI.yaml) · [MRS](clash-domain/AI.mrs) |
| AI | `ipcidr` | 23 | 🗨️ ChatGPT | [YAML](clash-ipcidr/AI-ipcidr.yaml) · [MRS](clash-ipcidr/AI-ipcidr.mrs) |
| AI | `classical` | 8 | 🗨️ ChatGPT | [YAML](clash-classic/AI-classic.yaml) |
| TikTok | `domain` | 58 | 📱 TikTok | [YAML](clash-domain/TikTok.yaml) · [MRS](clash-domain/TikTok.mrs) |
| TikTok | `classical` | 3 | 📱 TikTok | [YAML](clash-classic/TikTok-classic.yaml) |
| Bilibili | `domain` | 1,161 | 📺 哔哩哔哩 | [YAML](clash-domain/Bilibili.yaml) · [MRS](clash-domain/Bilibili.mrs) |
| Bilibili | `ipcidr` | 9 | 📺 哔哩哔哩 | [YAML](clash-ipcidr/Bilibili-ipcidr.yaml) · [MRS](clash-ipcidr/Bilibili-ipcidr.mrs) |
| Bilibili | `classical` | 7 | 📺 哔哩哔哩 | [YAML](clash-classic/Bilibili-classic.yaml) |
| Tencent | `domain` | 2,597 | DIRECT | [YAML](clash-domain/Tencent.yaml) · [MRS](clash-domain/Tencent.mrs) |
| Tencent | `ipcidr` | 52 | DIRECT | [YAML](clash-ipcidr/Tencent-ipcidr.yaml) · [MRS](clash-ipcidr/Tencent-ipcidr.mrs) |
| Tencent | `classical` | 1 | DIRECT | [YAML](clash-classic/Tencent-classic.yaml) |
| Netflix | `domain` | 32 | 🎬 Netflix | [YAML](clash-domain/Netflix.yaml) · [MRS](clash-domain/Netflix.mrs) |
| Netflix | `ipcidr` | 1,121 | 🎬 Netflix | [YAML](clash-ipcidr/Netflix-ipcidr.yaml) · [MRS](clash-ipcidr/Netflix-ipcidr.mrs) |
| Netflix | `classical` | 5 | 🎬 Netflix | [YAML](clash-classic/Netflix-classic.yaml) |
| YouTube | `domain` | 180 | 💻 YouTube | [YAML](clash-domain/YouTube.yaml) · [MRS](clash-domain/YouTube.mrs) |
| YouTube | `ipcidr` | 3 | 💻 YouTube | [YAML](clash-ipcidr/YouTube-ipcidr.yaml) · [MRS](clash-ipcidr/YouTube-ipcidr.mrs) |
| YouTube | `classical` | 1 | 💻 YouTube | [YAML](clash-classic/YouTube-classic.yaml) |
| Google | `domain` | 879 | 📩 Google | [YAML](clash-domain/Google.yaml) · [MRS](clash-domain/Google.mrs) |
| Google | `ipcidr` | 7,979 | 📩 Google | [YAML](clash-ipcidr/Google-ipcidr.yaml) · [MRS](clash-ipcidr/Google-ipcidr.mrs) |
| Google | `classical` | 11 | 📩 Google | [YAML](clash-classic/Google-classic.yaml) |
| Telegram | `domain` | 28 | 🛸 Telegram | [YAML](clash-domain/Telegram.yaml) · [MRS](clash-domain/Telegram.mrs) |
| Telegram | `ipcidr` | 14 | 🛸 Telegram | [YAML](clash-ipcidr/Telegram-ipcidr.yaml) · [MRS](clash-ipcidr/Telegram-ipcidr.mrs) |
| Telegram | `classical` | 12 | 🛸 Telegram | [YAML](clash-classic/Telegram-classic.yaml) |
| Japan | `domain` | 285 | 🌺 日本专线 | [YAML](clash-domain/Japan.yaml) · [MRS](clash-domain/Japan.mrs) |
| Japan | `ipcidr` | 19 | 🌺 日本专线 | [YAML](clash-ipcidr/Japan-ipcidr.yaml) · [MRS](clash-ipcidr/Japan-ipcidr.mrs) |
| Japan | `classical` | 4 | 🌺 日本专线 | [YAML](clash-classic/Japan-classic.yaml) |
| HK | `domain` | 1,296 | 🛫 香港专线 | [YAML](clash-domain/HK.yaml) · [MRS](clash-domain/HK.mrs) |
| HK | `ipcidr` | 2,715 | 🛫 香港专线 | [YAML](clash-ipcidr/HK-ipcidr.yaml) · [MRS](clash-ipcidr/HK-ipcidr.mrs) |
| HK | `classical` | 6 | 🛫 香港专线 | [YAML](clash-classic/HK-classic.yaml) |
| Apple | `domain` | 1,561 | 🍎 Apple | [YAML](clash-domain/Apple.yaml) · [MRS](clash-domain/Apple.mrs) |
| Apple | `ipcidr` | 13 | 🍎 Apple | [YAML](clash-ipcidr/Apple-ipcidr.yaml) · [MRS](clash-ipcidr/Apple-ipcidr.mrs) |
| Apple | `classical` | 20 | 🍎 Apple | [YAML](clash-classic/Apple-classic.yaml) |
| Singapore | `domain` | 943 | 🧊 新加坡专线 | [YAML](clash-domain/Singapore.yaml) · [MRS](clash-domain/Singapore.mrs) |
| Singapore | `ipcidr` | 141 | 🧊 新加坡专线 | [YAML](clash-ipcidr/Singapore-ipcidr.yaml) · [MRS](clash-ipcidr/Singapore-ipcidr.mrs) |
| Singapore | `classical` | 7 | 🧊 新加坡专线 | [YAML](clash-classic/Singapore-classic.yaml) |
| America | `domain` | 1,685 | ⛳ 美国专线 | [YAML](clash-domain/America.yaml) · [MRS](clash-domain/America.mrs) |
| America | `classical` | 4 | ⛳ 美国专线 | [YAML](clash-classic/America-classic.yaml) |
| ChinaMedia | `domain` | 5,502 | DIRECT | [YAML](clash-domain/ChinaMedia.yaml) · [MRS](clash-domain/ChinaMedia.mrs) |
| ChinaMedia | `ipcidr` | 1,730 | DIRECT | [YAML](clash-ipcidr/ChinaMedia-ipcidr.yaml) · [MRS](clash-ipcidr/ChinaMedia-ipcidr.mrs) |
| ChinaMedia | `classical` | 15 | DIRECT | [YAML](clash-classic/ChinaMedia-classic.yaml) |
| OneDrive | `domain` | 672 | ⛅ OneDrive | [YAML](clash-domain/OneDrive.yaml) · [MRS](clash-domain/OneDrive.mrs) |
| OneDrive | `ipcidr` | 3 | ⛅ OneDrive | [YAML](clash-ipcidr/OneDrive-ipcidr.yaml) · [MRS](clash-ipcidr/OneDrive-ipcidr.mrs) |
| OneDrive | `classical` | 9 | ⛅ OneDrive | [YAML](clash-classic/OneDrive-classic.yaml) |
| Microsoft | `domain` | 763 | 🪟 Microsoft | [YAML](clash-domain/Microsoft.yaml) · [MRS](clash-domain/Microsoft.mrs) |
| Microsoft | `classical` | 7 | 🪟 Microsoft | [YAML](clash-classic/Microsoft-classic.yaml) |
| Media | `domain` | 11,104 | 🛖 国际流媒体 | [YAML](clash-domain/Media.yaml) · [MRS](clash-domain/Media.mrs) |
| Media | `ipcidr` | 1,439 | 🛖 国际流媒体 | [YAML](clash-ipcidr/Media-ipcidr.yaml) · [MRS](clash-ipcidr/Media-ipcidr.mrs) |
| Media | `classical` | 42 | 🛖 国际流媒体 | [YAML](clash-classic/Media-classic.yaml) |
| Proxy | `domain` | 29,848 | 🌠 节点选择 | [YAML](clash-domain/Proxy.yaml) · [MRS](clash-domain/Proxy.mrs) |
| Proxy | `ipcidr` | 119 | 🌠 节点选择 | [YAML](clash-ipcidr/Proxy-ipcidr.yaml) · [MRS](clash-ipcidr/Proxy-ipcidr.mrs) |
| Proxy | `classical` | 39 | 🌠 节点选择 | [YAML](clash-classic/Proxy-classic.yaml) |
| China | `domain` | 110,750 | DIRECT | [YAML](clash-domain/China.yaml) · [MRS](clash-domain/China.mrs) |
| China | `ipcidr` | 12,558 | DIRECT | [YAML](clash-ipcidr/China-ipcidr.yaml) · [MRS](clash-ipcidr/China-ipcidr.mrs) |
| China | `classical` | 101 | DIRECT | [YAML](clash-classic/China-classic.yaml) |

「维护者的用法」只是参考：维护者有多个地区的节点，会把面向不同地区的规则集分别指向对应的地区组。你的节点布局不同，按自己的情况安排即可。

## 格式

- **MRS**：Mihomo 的二进制规则集，体积小、加载快，适合直接交给 Mihomo；不能阅读。只有 `domain` 与 `ipcidr` 有 MRS。
- **YAML**：标准的 rule-provider（`payload:`），带来源注释，适合阅读、审查，或作为你自己构建流程的上游；Mihomo 同样可以直接加载。
- `behavior` 由目录决定：`clash-domain` → `domain`，`clash-ipcidr` → `ipcidr`，`clash-classic` → `classical`。

## 下载地址

把 `<文件>` 换成上表中的路径：

- GitHub：`https://raw.githubusercontent.com/angwz/domainrouter_v2/release/<文件>`
- jsDelivr：`https://cdn.jsdelivr.net/gh/angwz/domainrouter_v2@release/<文件>`（国内访问较快；CDN 缓存，内容最多可能晚约 12 小时）

## 取用方式

### 挑几个规则集，用在 Mihomo 中

每个文件就是一个 rule-provider。

**MRS**：domain、ipcidr 用 MRS，classical 仍用 YAML：

```yaml
rule-providers:
  Direct:
    type: http
    behavior: domain
    format: mrs
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-domain/Direct.mrs
    path: ./rule-providers/Direct.mrs
    interval: 86400
  Direct-ipcidr:
    type: http
    behavior: ipcidr
    format: mrs
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-ipcidr/Direct-ipcidr.mrs
    path: ./rule-providers/Direct-ipcidr.mrs
    interval: 86400
  Direct-classic:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-classic/Direct-classic.yaml
    path: ./rule-providers/Direct-classic.yaml
    interval: 86400

rules:
  - RULE-SET,Direct,DIRECT
  - RULE-SET,Direct-ipcidr,DIRECT,no-resolve
  - RULE-SET,Direct-classic,DIRECT
```

**YAML**：全部使用 YAML，写法与 MRS 版只差 `format` 与扩展名：

```yaml
rule-providers:
  Direct:
    type: http
    behavior: domain
    format: yaml
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-domain/Direct.yaml
    path: ./rule-providers/Direct.yaml
    interval: 86400
  Direct-ipcidr:
    type: http
    behavior: ipcidr
    format: yaml
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-ipcidr/Direct-ipcidr.yaml
    path: ./rule-providers/Direct-ipcidr.yaml
    interval: 86400
  Direct-classic:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-classic/Direct-classic.yaml
    path: ./rule-providers/Direct-classic.yaml
    interval: 86400

rules:
  - RULE-SET,Direct,DIRECT
  - RULE-SET,Direct-ipcidr,DIRECT,no-resolve
  - RULE-SET,Direct-classic,DIRECT
```

策略组按自己的节点填写，规则的先后就是匹配优先级。只有一两个地区的节点时，面向其他地区的规则集可以指向同一个代理组，或者干脆不引用。

### 作为你的上游

把 YAML 地址交给你自己的规则工具即可。转换时请按 Mihomo 的语义理解域名写法：`+.example.com` 是自身及全部子域，`.example.com` 只匹配子域，`example.com` 只匹配自身。

下游最终交给 Mihomo、且不需要再加工时，可以直接引用 MRS，省去一次转换。

如果你也使用 DomainRouter v2，在 `my.wei` 中引用 YAML 并写明格式：

```text
@source https://raw.githubusercontent.com/angwz/domainrouter_v2/release/clash-domain/Direct.yaml format=domain
```

### 整套照搬（subconverter）

维护者自用的完整配置：`rulesets` 列出全部规则集及其指向的策略组，[groups.toml](groups.toml) 定义这些策略组。

| 版本 | rulesets | 引用的规则文件 |
| --- | --- | --- |
| YAML | [rulesets.toml](rulesets.toml) · `https://raw.githubusercontent.com/angwz/domainrouter_v2/release/rulesets.toml` | 全部为 YAML |
| MRS | [rulesets-mrs.toml](rulesets-mrs.toml) · `https://raw.githubusercontent.com/angwz/domainrouter_v2/release/rulesets-mrs.toml` | domain、ipcidr 为 MRS，classical 为 YAML |

两个版本的规则集条目与顺序完全相同，共用同一份 `https://raw.githubusercontent.com/angwz/domainrouter_v2/release/groups.toml`。MRS 版要求 subconverter 为 `.mrs` 引用写出 `format: mrs`：Mihomo 不按扩展名判断格式，未写 `format` 时一律按 YAML 读取。

`groups.toml` 中的组是按维护者多个地区的节点编排的。节点布局不同时，建议复制一份 `groups.toml` 按自己的节点调整，保留 `rulesets` 引用到的组名；需要改动规则本身时，fork [本项目](https://github.com/angwz/domainrouter_v2) 生成你自己的发布。
