# 宽泛规则：过滤与提醒

有些规则的匹配范围大到失去了分流意义，例如 `DOMAIN-KEYWORD,ads` 会命中 `uploads`、`downloads`、`roads`，`IP-CIDR,0.0.0.0/0` 会命中所有 IPv4 流量。上游规则剥掉策略字段后，这类条目会把大量无关流量带进你的策略组。

每次构建都会检查每一条规则，并把结果分成三个等级：

| 等级 | 含义 | 上游规则 | 手写规则 |
| --- | --- | --- | --- |
| 普通 | 范围正常 | 保留 | 保留 |
| 宽泛 | 范围大，但可能是有意的（品牌关键词、GEOIP、`+.cn`、进程……） | 保留，列入清单 | 保留，列入清单 |
| 过宽 | 接近全部流量，或使用了通用词关键词 | **过滤**，列入清单 | 保留，列入清单并告警 |

清单随规则文件一起发布在 release 分支的 `reports/broad-rules.md`。每次更新说明 `reports/latest.md` 的「宽泛规则」一节会列出本次被过滤的规则，以及新出现的宽泛规则。YAML 文件里不做逐条标注：Mihomo 会跳过整行注释，但行尾注释会影响解析。

如果确实需要某条被过滤的规则，把它手写进 my.wei 的相应合集。手写规则永远不会被过滤（[decisions/0002](../decisions/0002-filter-broad-upstream-rules.md)）。

实现见 `src/domainrouter_v2/breadth.py`，案例测试见 `tests/test_breadth.py`。

## 判定规则

| 类别 | 过宽（上游过滤） | 宽泛（只提醒） |
| --- | --- | --- |
| DOMAIN-KEYWORD | 关键词 ≤ 2 个字符；或在[宽泛关键词表](#宽泛关键词表)中 | 其余全部；3～4 个字符的额外标为“短关键词” |
| DOMAIN-REGEX | 能匹配一组互不相关的探测主机名（如 `.*`） | 其余全部 |
| 整个公共后缀（domain、DOMAIN-SUFFIX、DOMAIN-WILDCARD） | 覆盖 `com`、`net`、`org`、`info`、`biz` 之一；或没有任何固定标签（`*.*`） | 覆盖其他公共后缀，如 `+.cn`、`+.ac.uk`、`+.apple`；`*`（单标签主机名） |
| 大网段（IP-CIDR、IP-CIDR6、SRC-IP-CIDR） | IPv4 短于 /8、IPv6 短于 /12 的公网网段，含 `0.0.0.0/0`、`::/0`、`2000::/3` | IPv4 /8、IPv6 /12～/16 的公网网段 |
| IP-SUFFIX | `/0` | 其余全部 |
| IP-ASN | — | 全部（整个自治系统） |
| GEOIP / GEOSITE | — | 全部（整个国家/地区或站点分类） |
| 进程与用户（PROCESS-\*、UID） | 通配或正则匹配所有进程 | 其余全部（该程序的全部流量） |
| 连接属性 | `NETWORK`；`DST-PORT` 包含 80 或 443；`IN-PORT`、`IN-TYPE`、`IN-USER`、`IN-NAME` | 其他端口条件、`DSCP`、来源地址类条件 |
| 逻辑规则 | AND 取子条件中最窄的等级，OR 取最宽的；NOT 取反一个普通条件即为过宽 | NOT 取反一个宽泛条件 |

完全落在本地或保留地址块内的网段（`10.0.0.0/8`、`224.0.0.0/3`、`fc00::/7` 等，取自 IANA 特殊用途地址注册表中“非全球可达”的条目）不算大网段：它们只涉及局域网与保留地址。

逻辑规则的例子：`AND,((NETWORK,UDP),(DST-PORT,443))` 是全部 QUIC 流量，判为过宽；`AND,((NETWORK,UDP),(DOMAIN,a.com))` 被 `DOMAIN` 限定，判为普通。

## 阈值依据

- **关键词长度**：AdGuard [HostlistCompiler](https://github.com/AdguardTeam/HostlistCompiler) 的 Validate 会丢弃短于 5 个字符的非精确模式（`src/transformations/validate.js` 的 `MAX_PATTERN_LENGTH = 5`）。DOMAIN-KEYWORD 正是非精确的子串模式。这里更保守：≤ 2 个字符才过滤，3～4 个字符只提醒。
- **整个顶级域**：HostlistCompiler 同样会删除覆盖整个顶级域的规则（如 `||*.org^`）。分流场景下 ccTLD（`+.cn`）和品牌 TLD（`+.apple`）常是有意的，所以只过滤不限地域、不限用途的通用顶级域。
- **公共后缀**：判断依据是 [Public Suffix List](https://publicsuffix.org/) 的 ICANN 段（提交 `7a21dc3`），已打包在 `src/domainrouter_v2/data/public_suffix_icann.txt`，并按 PSL 算法处理 `*` 与 `!` 规则。PRIVATE 段（如 `github.io`）不参与判断：覆盖它的规则通常是有意针对某个服务。
- **网段**：区域互联网注册管理机构（RIR）从 IANA 获得地址块，IPv4 以 /8、IPv6 以 /12 为单位。比这更大的公网网段跨越多个 RIR 的分配，不可能对应某一个服务。
- **端口 80/443**：所有网页流量都经过这两个端口，按端口分流等于不看目标。
- **入站条件**：按入站区分的规则会命中该入站的全部流量，不应出现在上游规则集中。

## 宽泛关键词表

文件：`src/domainrouter_v2/data/broad_keywords.txt`，每行一个词。上游 DOMAIN-KEYWORD 的关键词转小写、去掉首尾的 `.` 和 `-` 后，与表中某个词完全相同时，整条规则被过滤。比较只看整词：`uploads` 不会因为表里有 `ads` 而被过滤。

收录原则：只收通用词，不收品牌名。`google`、`telegram` 这类关键词同样会误伤，例如它们也是常见的子域名，但它们通常是规则作者有意为之，所以只列入清单。来源：

- **[A] 最常见的 DNS 标签**：[SecLists](https://github.com/danielmiessler/SecLists) 的 `Discovery/DNS/subdomains-top1million-5000.txt`（提交 `6106054`，MIT），从前 1000 名中挑出通用词。例如 `ads` 排第 222 名，`analytics` 第 201 名，`tracker` 第 548 名。这些词本身就是大量网站的子域名，作为关键词几乎必然误伤。
- **[B] 主流规则集中实际出现的通用词**：blackmatrix7/ios_rule_script 的 Advertising 规则与 ACL4SSR 的 BanAD 规则里，作为 DOMAIN-KEYWORD 出现的 `advert`、`adserver`、`adservice`、`adsystem`，以及拼音 `guanggao`（广告）、`fenxi`（分析）。[ClashX 规则指南](https://clashx-web.pages.dev/en/article-5)也以 `DOMAIN-KEYWORD,ads` 为例，提示“谨慎使用”。

维护方式：直接编辑该文件，在相应分节下加词并注明依据。修改后重新构建即可生效；关键词表与 PSL 的内容会计入 `manifest.json` 的引擎指纹。

## 限制

- DOMAIN-REGEX 用 Python `re` 近似判断能否匹配一切。Mihomo 使用 Go RE2，两者语法有少量差异；Python 无法编译的正则只提醒，不过滤。
- 过滤会缩小来自上游的匹配集合，这是有意的改动。验证层（语义层与内核层）对照的是过滤之后、优化前后的结果，证明的是优化等价，不覆盖过滤本身；过滤的内容由清单逐条列出。
- 判定只看规则本身，不看它所在的合集或策略组。
