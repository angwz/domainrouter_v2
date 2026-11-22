# 规则更新说明

- 生成时间（UTC）：2026-11-22T01:53:10+00:00
- generation：`cd0972a75149e49b`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 0 条。完整清单见 [broad-rules.md](broad-rules.md)。

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-domain/Proxy.yaml` | 29854 → 29872 | 19 | 1 |

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（19）：

```text
+.cmoney.tw
+.gamma.app
+.greenbean.media
+.hkcitycreation.com
+.hkcourtnews.com
+.hkfeature.com
+.lifesitenews.com
+.master-insight.com
+.moneynet.com.tw
+.my-formosa.com.tw
+.pulsehknews.com
+.shanghainationalparty.com
+.soulogic.com
+.taiwantoday.tw
+.thecollectivehk.com
+.theonlinecitizen.com
+.thestar.com
+.thewitnesshk.com
+.womany.net
```

删除（1）：

```text
+.cnshopin.com
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3778 | 2566 | 347 | 22 | 859 |
| NS | 9 | 8 | 1 | 0 | 0 |
| AI | 850 | 338 | 466 | 22 | 39 |
| TikTok | 75 | 61 | 12 | 2 | 0 |
| Bilibili | 1539 | 1177 | 310 | 48 | 8 |
| Tencent | 3376 | 2650 | 558 | 167 | 0 |
| Netflix | 1303 | 1158 | 24 | 0 | 122 |
| YouTube | 361 | 184 | 176 | 1 | 0 |
| Google | 8869 | 7980 | 612 | 217 | 85 |
| Telegram | 97 | 54 | 33 | 0 | 10 |
| Japan | 545 | 308 | 194 | 42 | 0 |
| HK | 5099 | 4018 | 784 | 44 | 288 |
| Apple | 3468 | 1594 | 1428 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 2509 | 1693 | 631 | 179 | 8 |
| ChinaMedia | 9981 | 7252 | 2223 | 426 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13885 | 12585 | 1001 | 262 | 55 |
| Proxy | 69469 | 30030 | 32797 | 6540 | 102 |
| China | 506861 | 123422 | 337589 | 72 | 45779 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
