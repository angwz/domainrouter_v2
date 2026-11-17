# 规则更新说明

- 生成时间（UTC）：2026-11-17T04:18:37+00:00
- generation：`e7a17e0ba4d14a7b`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 0 条。完整清单见 [broad-rules.md](broad-rules.md)。

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-domain/America.yaml` | 1685 → 1689 | 4 | 0 |
| `clash-domain/Proxy.yaml` | 29849 → 29851 | 2 | 0 |
| `clash-domain/Singapore.yaml` | 943 → 944 | 1 | 0 |

<details>
<summary><code>clash-domain/America.yaml</code></summary>

新增（4）：

```text
builds.dotnet.microsoft.com
dotnetcli.trafficmanager.net
sundry-star-net-geo.trafficmanager.net
vscode.download.prss.microsoft.com
```

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（2）：

```text
+.debot.ai
+.remna.dev
```

</details>

<details>
<summary><code>clash-domain/Singapore.yaml</code></summary>

新增（1）：

```text
+.debot.ai
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3775 | 2563 | 347 | 22 | 859 |
| NS | 9 | 8 | 1 | 0 | 0 |
| AI | 846 | 337 | 465 | 21 | 37 |
| TikTok | 75 | 61 | 12 | 2 | 0 |
| Bilibili | 1539 | 1177 | 310 | 48 | 8 |
| Tencent | 3375 | 2650 | 557 | 167 | 0 |
| Netflix | 1303 | 1158 | 24 | 0 | 122 |
| YouTube | 361 | 184 | 176 | 1 | 0 |
| Google | 9758 | 8869 | 612 | 217 | 85 |
| Telegram | 97 | 54 | 33 | 0 | 10 |
| Japan | 545 | 308 | 194 | 42 | 0 |
| HK | 5098 | 4017 | 784 | 44 | 288 |
| Apple | 3598 | 1594 | 1558 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 2509 | 1693 | 631 | 179 | 8 |
| ChinaMedia | 9972 | 7247 | 2220 | 425 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13885 | 12585 | 1001 | 262 | 55 |
| Proxy | 69578 | 30009 | 32927 | 6540 | 102 |
| China | 506836 | 123409 | 337589 | 72 | 45767 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
