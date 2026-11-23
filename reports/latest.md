# 规则更新说明

- 生成时间（UTC）：2026-11-23T02:09:04+00:00
- generation：`bf2bc5ec45e21f0d`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 2 条。完整清单见 [broad-rules.md](broad-rules.md)。

| 新发布 | 说明 | 文件 |
| --- | --- | --- |
| `+.hkt` | 覆盖公共后缀 .hkt 下的域名 | `clash-domain/Proxy.yaml` |
| `+.pccw` | 覆盖公共后缀 .pccw 下的域名 | `clash-domain/Proxy.yaml` |

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-domain/America.yaml` | 1689 → 1691 | 2 | 0 |
| `clash-domain/Media.yaml` | 11104 → 11121 | 19 | 2 |
| `clash-domain/Proxy.yaml` | 29872 → 29896 | 24 | 0 |

<details>
<summary><code>clash-domain/America.yaml</code></summary>

新增（2）：

```text
+.replit.com
+.tortoisegit.org
```

</details>

<details>
<summary><code>clash-domain/Media.yaml</code></summary>

新增（19）：

```text
+.51papaya.com
+.cnbccouncils.com
+.fanza.jp
+.focusfeatures.com
+.hayu.com
+.illumination.com
+.nbcumv.com
+.nbcunicareers.com
+.nbcuniversalprivacy.com
+.udxfpp.com
+.universalbeijingresort.com
+.universalhorrorunleashed.com
+.universalkidsresort.com
+.universalpictures.co.uk
+.universalpicturesathome.com
+.universalproductsexperiences.com
+.universalukproject.co.uk
+.uphe.com
+.usj.co.jp
```

删除（2）：

```text
+.imagetwist.com
+.mycdn.me
```

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（24）：

```text
+.bravotv.com
+.cnbccouncils.com
+.fanza.jp
+.focusfeatures.com
+.hayu.com
+.hkt
+.illumination.com
+.nbcumv.com
+.nbcunicareers.com
+.nbcuniversalprivacy.com
+.pccw
+.replit.com
+.telemundo.com
+.tortoisegit.org
+.udxfpp.com
+.universalbeijingresort.com
+.universalhorrorunleashed.com
+.universalkidsresort.com
+.universalpictures.co.uk
+.universalpicturesathome.com
+.universalproductsexperiences.com
+.universalukproject.co.uk
+.uphe.com
+.usj.co.jp
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
| Japan | 547 | 308 | 195 | 43 | 0 |
| HK | 5099 | 4018 | 784 | 44 | 288 |
| Apple | 3468 | 1594 | 1428 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 2511 | 1695 | 631 | 179 | 8 |
| ChinaMedia | 9981 | 7252 | 2223 | 426 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13903 | 12602 | 1002 | 262 | 55 |
| Proxy | 69492 | 30054 | 32796 | 6540 | 102 |
| China | 506861 | 123422 | 337589 | 72 | 45779 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
