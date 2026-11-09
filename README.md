# DomainRouter v2 · 规则发布

这里是 [DomainRouter v2](https://github.com/angwz/domainrouter_v2) 每天自动生成的规则，欢迎自由取用。
规则按维护者的分流偏好整理，可能随时调整；规则数据来自各上游规则集，适用其原有条款。

- **更新**：每天北京时间 06:00 前后，内容没有变化时不产生新提交。
- **说明**：本次更新说明见 [reports/latest.md](reports/latest.md)，范围较大的规则见 [reports/broad-rules.md](reports/broad-rules.md)。
- **来历**：每个文件开头列出来源，每条规则的同行注释标出它来自哪个上游。

## 规则一览

| 规则集 | behavior | 条目 | 维护者的用法 | 文件 |
| --- | --- | ---: | --- | --- |
| Direct | `domain` | 1,979 | DIRECT | [clash-domain/Direct.yaml](clash-domain/Direct.yaml) |
| Direct | `ipcidr` | 530 | DIRECT | [clash-ipcidr/Direct-ipcidr.yaml](clash-ipcidr/Direct-ipcidr.yaml) |
| Direct | `classical` | 53 | DIRECT | [clash-classic/Direct-classic.yaml](clash-classic/Direct-classic.yaml) |
| NS | `domain` | 7 | 🏖️ Community | [clash-domain/NS.yaml](clash-domain/NS.yaml) |
| NS | `classical` | 1 | 🏖️ Community | [clash-classic/NS-classic.yaml](clash-classic/NS-classic.yaml) |
| AI | `domain` | 304 | 🗨️ ChatGPT | [clash-domain/AI.yaml](clash-domain/AI.yaml) |
| AI | `ipcidr` | 23 | 🗨️ ChatGPT | [clash-ipcidr/AI-ipcidr.yaml](clash-ipcidr/AI-ipcidr.yaml) |
| AI | `classical` | 8 | 🗨️ ChatGPT | [clash-classic/AI-classic.yaml](clash-classic/AI-classic.yaml) |
| TikTok | `domain` | 58 | 📱 TikTok | [clash-domain/TikTok.yaml](clash-domain/TikTok.yaml) |
| TikTok | `classical` | 3 | 📱 TikTok | [clash-classic/TikTok-classic.yaml](clash-classic/TikTok-classic.yaml) |
| Bilibili | `domain` | 1,161 | 📺 哔哩哔哩 | [clash-domain/Bilibili.yaml](clash-domain/Bilibili.yaml) |
| Bilibili | `ipcidr` | 9 | 📺 哔哩哔哩 | [clash-ipcidr/Bilibili-ipcidr.yaml](clash-ipcidr/Bilibili-ipcidr.yaml) |
| Bilibili | `classical` | 7 | 📺 哔哩哔哩 | [clash-classic/Bilibili-classic.yaml](clash-classic/Bilibili-classic.yaml) |
| Tencent | `domain` | 2,597 | DIRECT | [clash-domain/Tencent.yaml](clash-domain/Tencent.yaml) |
| Tencent | `ipcidr` | 52 | DIRECT | [clash-ipcidr/Tencent-ipcidr.yaml](clash-ipcidr/Tencent-ipcidr.yaml) |
| Tencent | `classical` | 1 | DIRECT | [clash-classic/Tencent-classic.yaml](clash-classic/Tencent-classic.yaml) |
| Netflix | `domain` | 32 | 🎬 Netflix | [clash-domain/Netflix.yaml](clash-domain/Netflix.yaml) |
| Netflix | `ipcidr` | 1,121 | 🎬 Netflix | [clash-ipcidr/Netflix-ipcidr.yaml](clash-ipcidr/Netflix-ipcidr.yaml) |
| Netflix | `classical` | 5 | 🎬 Netflix | [clash-classic/Netflix-classic.yaml](clash-classic/Netflix-classic.yaml) |
| YouTube | `domain` | 180 | 💻 YouTube | [clash-domain/YouTube.yaml](clash-domain/YouTube.yaml) |
| YouTube | `ipcidr` | 3 | 💻 YouTube | [clash-ipcidr/YouTube-ipcidr.yaml](clash-ipcidr/YouTube-ipcidr.yaml) |
| YouTube | `classical` | 1 | 💻 YouTube | [clash-classic/YouTube-classic.yaml](clash-classic/YouTube-classic.yaml) |
| Google | `domain` | 879 | 📩 Google | [clash-domain/Google.yaml](clash-domain/Google.yaml) |
| Google | `ipcidr` | 8,426 | 📩 Google | [clash-ipcidr/Google-ipcidr.yaml](clash-ipcidr/Google-ipcidr.yaml) |
| Google | `classical` | 11 | 📩 Google | [clash-classic/Google-classic.yaml](clash-classic/Google-classic.yaml) |
| Telegram | `domain` | 28 | 🛸 Telegram | [clash-domain/Telegram.yaml](clash-domain/Telegram.yaml) |
| Telegram | `ipcidr` | 14 | 🛸 Telegram | [clash-ipcidr/Telegram-ipcidr.yaml](clash-ipcidr/Telegram-ipcidr.yaml) |
| Telegram | `classical` | 12 | 🛸 Telegram | [clash-classic/Telegram-classic.yaml](clash-classic/Telegram-classic.yaml) |
| Japan | `domain` | 285 | 🌺 日本专线 | [clash-domain/Japan.yaml](clash-domain/Japan.yaml) |
| Japan | `ipcidr` | 19 | 🌺 日本专线 | [clash-ipcidr/Japan-ipcidr.yaml](clash-ipcidr/Japan-ipcidr.yaml) |
| Japan | `classical` | 4 | 🌺 日本专线 | [clash-classic/Japan-classic.yaml](clash-classic/Japan-classic.yaml) |
| HK | `domain` | 1,296 | 🛫 香港专线 | [clash-domain/HK.yaml](clash-domain/HK.yaml) |
| HK | `ipcidr` | 2,715 | 🛫 香港专线 | [clash-ipcidr/HK-ipcidr.yaml](clash-ipcidr/HK-ipcidr.yaml) |
| HK | `classical` | 6 | 🛫 香港专线 | [clash-classic/HK-classic.yaml](clash-classic/HK-classic.yaml) |
| Apple | `domain` | 1,561 | 🍎 Apple | [clash-domain/Apple.yaml](clash-domain/Apple.yaml) |
| Apple | `ipcidr` | 13 | 🍎 Apple | [clash-ipcidr/Apple-ipcidr.yaml](clash-ipcidr/Apple-ipcidr.yaml) |
| Apple | `classical` | 20 | 🍎 Apple | [clash-classic/Apple-classic.yaml](clash-classic/Apple-classic.yaml) |
| Singapore | `domain` | 943 | 🧊 新加坡专线 | [clash-domain/Singapore.yaml](clash-domain/Singapore.yaml) |
| Singapore | `ipcidr` | 142 | 🧊 新加坡专线 | [clash-ipcidr/Singapore-ipcidr.yaml](clash-ipcidr/Singapore-ipcidr.yaml) |
| Singapore | `classical` | 7 | 🧊 新加坡专线 | [clash-classic/Singapore-classic.yaml](clash-classic/Singapore-classic.yaml) |
| America | `domain` | 1,683 | ⛳ 美国专线 | [clash-domain/America.yaml](clash-domain/America.yaml) |
| America | `classical` | 4 | ⛳ 美国专线 | [clash-classic/America-classic.yaml](clash-classic/America-classic.yaml) |
| ChinaMedia | `domain` | 5,502 | DIRECT | [clash-domain/ChinaMedia.yaml](clash-domain/ChinaMedia.yaml) |
| ChinaMedia | `ipcidr` | 1,730 | DIRECT | [clash-ipcidr/ChinaMedia-ipcidr.yaml](clash-ipcidr/ChinaMedia-ipcidr.yaml) |
| ChinaMedia | `classical` | 15 | DIRECT | [clash-classic/ChinaMedia-classic.yaml](clash-classic/ChinaMedia-classic.yaml) |
| OneDrive | `domain` | 672 | ⛅ OneDrive | [clash-domain/OneDrive.yaml](clash-domain/OneDrive.yaml) |
| OneDrive | `ipcidr` | 3 | ⛅ OneDrive | [clash-ipcidr/OneDrive-ipcidr.yaml](clash-ipcidr/OneDrive-ipcidr.yaml) |
| OneDrive | `classical` | 9 | ⛅ OneDrive | [clash-classic/OneDrive-classic.yaml](clash-classic/OneDrive-classic.yaml) |
| Microsoft | `domain` | 763 | 🪟 Microsoft | [clash-domain/Microsoft.yaml](clash-domain/Microsoft.yaml) |
| Microsoft | `classical` | 7 | 🪟 Microsoft | [clash-classic/Microsoft-classic.yaml](clash-classic/Microsoft-classic.yaml) |
| Media | `domain` | 11,104 | 🛖 国际流媒体 | [clash-domain/Media.yaml](clash-domain/Media.yaml) |
| Media | `ipcidr` | 1,439 | 🛖 国际流媒体 | [clash-ipcidr/Media-ipcidr.yaml](clash-ipcidr/Media-ipcidr.yaml) |
| Media | `classical` | 42 | 🛖 国际流媒体 | [clash-classic/Media-classic.yaml](clash-classic/Media-classic.yaml) |
| Proxy | `domain` | 29,844 | 🌠 节点选择 | [clash-domain/Proxy.yaml](clash-domain/Proxy.yaml) |
| Proxy | `ipcidr` | 119 | 🌠 节点选择 | [clash-ipcidr/Proxy-ipcidr.yaml](clash-ipcidr/Proxy-ipcidr.yaml) |
| Proxy | `classical` | 39 | 🌠 节点选择 | [clash-classic/Proxy-classic.yaml](clash-classic/Proxy-classic.yaml) |
| China | `domain` | 110,750 | DIRECT | [clash-domain/China.yaml](clash-domain/China.yaml) |
| China | `ipcidr` | 12,569 | DIRECT | [clash-ipcidr/China-ipcidr.yaml](clash-ipcidr/China-ipcidr.yaml) |
| China | `classical` | 101 | DIRECT | [clash-classic/China-classic.yaml](clash-classic/China-classic.yaml) |

## 下载地址

把下面地址中的 `<文件>` 换成上表中的路径：

- GitHub：`https://raw.githubusercontent.com/angwz/domainrouter_v2/release/<文件>`
- jsDelivr 加速：`https://cdn.jsdelivr.net/gh/angwz/domainrouter_v2@release/<文件>`（CDN 缓存，内容最多可能晚约 12 小时）

## 在 Mihomo 中使用

每个文件是一个 rule-provider。`behavior` 按目录选择：`clash-domain` → `domain`，`clash-ipcidr` → `ipcidr`，`clash-classic` → `classical`；文件都是 YAML 格式。

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

策略组按自己的配置填写；规则之间的先后就是匹配优先级。

## 在 subconverter 中使用

[rulesets.toml](rulesets.toml) 与 [groups.toml](groups.toml) 是维护者自用的完整配置，可以直接引用：

- `https://raw.githubusercontent.com/angwz/domainrouter_v2/release/rulesets.toml`
- `https://raw.githubusercontent.com/angwz/domainrouter_v2/release/groups.toml`

其中的策略组名称是维护者的命名；只想用部分规则时，从上表挑选文件写进自己的配置更合适。
