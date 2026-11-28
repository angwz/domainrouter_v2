# 规则更新说明

- 生成时间（UTC）：2026-11-28T04:39:24+00:00
- generation：`3c3d103203182267`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 1 条。完整清单见 [broad-rules.md](broad-rules.md)。

| 新发布 | 说明 | 文件 |
| --- | --- | --- |
| `AND,((DST-PORT,5223),(IP-CIDR,17.0.0.0/8,no-resolve))` | AND：不区分目标，按连接属性匹配；/8 大网段 | `clash-classic/Telegram-classic.yaml` |

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-classic/Telegram-classic.yaml` | 12 → 13 | 1 | 0 |
| `clash-domain/ChinaMedia.yaml` | 5511 → 5512 | 1 | 0 |
| `clash-domain/OneDrive.yaml` | 672 → 672 | 3 | 3 |
| `clash-domain/Proxy.yaml` | 29913 → 29917 | 4 | 0 |
| `clash-domain/Telegram.yaml` | 28 → 31 | 3 | 0 |
| `clash-ipcidr/Telegram-ipcidr.yaml` | 14 → 19 | 5 | 0 |

<details>
<summary><code>clash-classic/Telegram-classic.yaml</code></summary>

新增（1）：

```text
AND,((DST-PORT,5223),(IP-CIDR,17.0.0.0/8,no-resolve))
```

</details>

<details>
<summary><code>clash-domain/ChinaMedia.yaml</code></summary>

新增（1）：

```text
+.fce.gg
```

</details>

<details>
<summary><code>clash-domain/OneDrive.yaml</code></summary>

新增（3）：

```text
+.opentracker.xyz
+.opentrackr.org
+.zer0day.ch
```

删除（3）：

```text
opentrackr.org
tracker.opentrackr.org
zer0day.ch
```

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（4）：

```text
+.aicu.cc
+.danmakus.com
+.fce.gg
+.spacedesk.net
```

</details>

<details>
<summary><code>clash-domain/Telegram.yaml</code></summary>

新增（3）：

```text
+.courier-push-apple.com.akadns.net
+.push-apple.com.akadns.net
+.push.apple.com
```

</details>

<details>
<summary><code>clash-ipcidr/Telegram-ipcidr.yaml</code></summary>

新增（5）：

```text
17.188.128.0/18
17.188.20.0/23
17.249.0.0/16
17.252.0.0/16
17.57.144.0/22
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3778 | 2566 | 347 | 22 | 859 |
| NS | 9 | 8 | 1 | 0 | 0 |
| AI | 852 | 339 | 468 | 21 | 39 |
| TikTok | 75 | 61 | 12 | 2 | 0 |
| Bilibili | 1539 | 1177 | 310 | 48 | 8 |
| Tencent | 3376 | 2650 | 558 | 167 | 0 |
| Netflix | 1303 | 1158 | 24 | 0 | 122 |
| YouTube | 361 | 184 | 176 | 1 | 0 |
| Google | 8695 | 7806 | 612 | 217 | 85 |
| Telegram | 106 | 63 | 33 | 0 | 10 |
| Japan | 547 | 308 | 195 | 43 | 0 |
| HK | 4618 | 3784 | 540 | 42 | 286 |
| Apple | 3468 | 1594 | 1428 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 3010 | 1939 | 877 | 187 | 10 |
| ChinaMedia | 9987 | 7257 | 2224 | 426 | 117 |
| OneDrive | 1087 | 684 | 384 | 14 | 10 |
| Microsoft | 1512 | 771 | 611 | 123 | 14 |
| Media | 13903 | 12602 | 1002 | 262 | 55 |
| Proxy | 69514 | 30075 | 32796 | 6541 | 102 |
| China | 506931 | 123435 | 337589 | 72 | 45836 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
