# 规则更新说明

- 生成时间（UTC）：2026-11-26T03:54:15+00:00
- generation：`2a695324d5295c73`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 0 条。完整清单见 [broad-rules.md](broad-rules.md)。

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-domain/America.yaml` | 1691 → 1694 | 3 | 0 |
| `clash-domain/Proxy.yaml` | 29897 → 29902 | 5 | 0 |

<details>
<summary><code>clash-domain/America.yaml</code></summary>

新增（3）：

```text
+.cachix.org
+.debian.map.fastlydns.net
+.vivox.com
```

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（5）：

```text
+.cachix.org
+.fastly-insights.com
+.fastlydns.net
+.vivox.com
courses.myecnu.org
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3778 | 2566 | 347 | 22 | 859 |
| NS | 9 | 8 | 1 | 0 | 0 |
| AI | 855 | 341 | 468 | 22 | 39 |
| TikTok | 75 | 61 | 12 | 2 | 0 |
| Bilibili | 1539 | 1177 | 310 | 48 | 8 |
| Tencent | 3376 | 2650 | 558 | 167 | 0 |
| Netflix | 1303 | 1158 | 24 | 0 | 122 |
| YouTube | 361 | 184 | 176 | 1 | 0 |
| Google | 8870 | 7981 | 612 | 217 | 85 |
| Telegram | 97 | 54 | 33 | 0 | 10 |
| Japan | 547 | 308 | 195 | 43 | 0 |
| HK | 5112 | 4029 | 786 | 44 | 288 |
| Apple | 3468 | 1594 | 1428 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 2514 | 1698 | 631 | 179 | 8 |
| ChinaMedia | 9985 | 7256 | 2223 | 426 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13903 | 12602 | 1002 | 262 | 55 |
| Proxy | 69498 | 30060 | 32796 | 6540 | 102 |
| China | 506861 | 123422 | 337589 | 72 | 45779 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
