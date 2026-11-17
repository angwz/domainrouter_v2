# 规则更新说明

- 生成时间（UTC）：2026-11-17T16:44:12+00:00
- generation：`955784a30ad0d542`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 0 条。完整清单见 [broad-rules.md](broad-rules.md)。

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-domain/ChinaMedia.yaml` | 5502 → 5503 | 1 | 0 |
| `clash-domain/Proxy.yaml` | 29851 → 29853 | 2 | 0 |
| `clash-ipcidr/Direct-ipcidr.yaml` | 530 → 533 | 4 | 1 |
| `clash-ipcidr/HK-ipcidr.yaml` | 2715 → 2716 | 1 | 0 |

<details>
<summary><code>clash-domain/ChinaMedia.yaml</code></summary>

新增（1）：

```text
+.cygames.com
```

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（2）：

```text
+.cygames.com
+.yb-payment.ru
```

</details>

<details>
<summary><code>clash-ipcidr/Direct-ipcidr.yaml</code></summary>

新增（4）：

```text
156.238.126.0/24
166.0.16.0/24
2602:f506:81::/64
2602:f988:211:bd8::/64
```

删除（1）：

```text
207.56.18.0/24
```

</details>

<details>
<summary><code>clash-ipcidr/HK-ipcidr.yaml</code></summary>

新增（1）：

```text
2607:9d00:2000:137::/64
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3778 | 2566 | 347 | 22 | 859 |
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
| HK | 5099 | 4018 | 784 | 44 | 288 |
| Apple | 3598 | 1594 | 1558 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 2509 | 1693 | 631 | 179 | 8 |
| ChinaMedia | 9974 | 7248 | 2221 | 425 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13885 | 12585 | 1001 | 262 | 55 |
| Proxy | 69580 | 30011 | 32927 | 6540 | 102 |
| China | 506836 | 123409 | 337589 | 72 | 45767 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
