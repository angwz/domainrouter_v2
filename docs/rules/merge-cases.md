# 规则转换与合并案例

本文是 DomainRouter v2 处理规则的**语义契约**：每个案例都会成为自动化测试。案例格式为「输入 → 输出 → 原因」，依据列出官方文档或源码位置。

- 输出列使用最终发布的 Mihomo 写法：domain 集合条目、ipcidr 集合条目或 classical 行。
- 「跳过」表示该条不进入产物，并在每次运行的更新说明中列出原因。
- 目标内核版本：Mihomo v1.19.33（见 [docs/decisions/0001](../decisions/0001-deviations-from-spec-1.5.md)）。

## 1. 三类输出与匹配效率

Mihomo 对三类 rule-provider 的处理方式完全不同，这决定了所有转换的方向：

| 输出 | 内核数据结构 | 单次匹配成本 | 文件内顺序 |
| --- | --- | --- | --- |
| domain（`clash-domain/X.yaml`） | 紧凑反向 trie（DomainSet），加载时排序去重 | 与主机名长度相关，与条目数无关 | 不影响 |
| ipcidr（`clash-ipcidr/X-ipcidr.yaml`） | 有序区间 + 二分查找，加载时合并 | O(log n) | 不影响 |
| classical（`clash-classic/X-classic.yaml`） | 规则数组，逐条比对，首个命中即返回 | O(n) | 影响（越常命中、越便宜的越靠前越好） |

依据：`rules/provider/domain_strategy.go`、`ipcidr_strategy.go`、`classical_strategy.go`、`component/trie/domain_set.go`（mihomo v1.19.33）。

由此得到的转换原则：

1. **能进 domain/ipcidr 集合的一律进集合**。`DOMAIN`、`DOMAIN-SUFFIX`、各格式的精确/后缀域名都进 domain 集合；目标 `IP-CIDR`/`IP-CIDR6` 都进 ipcidr 集合。classical 只留集合表达不了的条件。
2. **IP 条件不触发 DNS**。上游规则中的目标 IP 条件一律带 `no-resolve`；ipcidr 集合的 `no-resolve` 由 subconverter 在 `RULE-SET` 引用上追加。
3. **classical 按成本排序**。provider 只返回「是否命中」，因此纯条件之间可以任意重排而不改变结果：

   | 次序 | 类型 | 理由 |
   | --- | --- | --- |
   | 1 | `NETWORK`、`DST-PORT`、`SRC-PORT`、`IN-*`、`DSCP` | 只读已有元数据 |
   | 2 | `SRC-IP-CIDR`、`SRC-IP-SUFFIX`、`SRC-GEOIP`、`SRC-IP-ASN` | 来源地址已知 |
   | 3 | `DOMAIN-KEYWORD` | 子串比较 |
   | 4 | `DOMAIN-WILDCARD` | glob 回溯 |
   | 5 | `GEOSITE` | 查已加载的 geosite 集合 |
   | 6 | `DOMAIN-REGEX` | regexp2 回溯引擎，最贵的字符串匹配 |
   | 7 | `GEOIP`、`IP-ASN`、`IP-SUFFIX`（均 `no-resolve`） | mmdb 查询 |
   | 8 | `AND`、`OR`、`NOT` | 内部可能含任意子条件 |
   | 9 | `PROCESS-NAME*`、`PROCESS-PATH*`、`UID` | 可能触发进程查询，放最后可避免已被前面命中的连接做查询 |

   同次序内按规范化文本字节序稳定排序，保证每天的产物可重复、diff 可读。
4. **集合内部的排序不影响速度**：Mihomo 加载时会把全部条目重新排序后建索引。文件中按覆盖范围从宽到窄排列，只是为了便于阅读和审查（见 §10）。
5. **减少 RULE-SET 条数**：`[Rules]` 中相邻且目标策略组相同的合集引用，合并为一组文件（见 §9）。

## 2. 手写 `my.wei` 的域名语义

手写自由行沿用规范 1.5 第 4.2 节（用户已确认的语义）。

| 输入 | 输出（domain 集合） | 原因 |
| --- | --- | --- |
| `a.hk` | `+.a.hk` | 裸域名包含自身与全部子域 |
| `'a.hk'` | `a.hk` | 单引号：仅自身 |
| `"a.hk"` | `+.a.hk` | 双引号只是外围容器 |
| `DOMAIN,a.hk` | `a.hk` | 显式精确 |
| `DOMAIN-SUFFIX,a.hk` | `+.a.hk` | 显式后缀 |
| `'*.a.hk'` | `*.a.hk` | 恰好一级子域 |
| `*.a.hk` | `.a.hk` | 一级通配 + 隐式子域闭包 → 全部子域，不含自身 |
| `'.a.hk'` / `.a.hk` | `.a.hk` | 仅子域 |
| `'+.a.hk'` / `+.a.hk` | `+.a.hk` | 自身与全部子域 |
| `'xbox.*.example.com'` | `xbox.*.example.com` | 中间一个完整标签 |
| `xbox.*.example.com` | `+.xbox.*.example.com` | 上一模式及全部下级 |
| `‘a.hk’`（中文引号成对） | `a.hk` | 规范化为语义单引号，记录修复 |
| `'a.hk`（不配对） | 报错 | 不能去掉引号后当裸域名 |
| `*`、`+`、`.` 单独一行 | 报错 | 歧义，不能默认成全匹配 |
| `foo*.example.com` | 报错，建议 `DOMAIN-WILDCARD,foo*.example.com` | 原生模式不支持局部标签通配 |
| `DOMAIN-SUFFIX,*.a.hk` | 报错 | 显式字段是字面域名，不能偷换成通配 |
| `A.HK.` | `+.a.hk` | 小写、去末尾根点，记录修复 |
| `例子.hk` | `+.xn--fsqu00a.hk` | UTS #46 非过渡映射转 A-label，记录修复 |

## 3. 来源格式：识别与转换

### 3.1 支持的格式

每个上游来源用 `@source URL format=名称` 指定格式；裸 URL 等价于 `format=auto`。只支持有官方文档的格式：

| `format=` | 格式 | 官方依据 |
| --- | --- | --- |
| `mihomo` | Mihomo rule-provider（yaml 或 text；behavior 自动判断） | <https://wiki.metacubex.one/en/config/rule-providers/content/> |
| `domain` / `ipcidr` / `classical` | 同上，显式指定 behavior | 同上 |
| `surge` | Surge 规则列表（RULE-SET 文件） | <https://manual.nssurge.com/rules/ruleset.html> |
| `surge-domainset` | Surge DOMAIN-SET 文件 | <https://manual.nssurge.com/rules/domain.html> |
| `loon` | Loon 规则列表 | <https://nsloon.app/docs/Rule/> |
| `singbox` | sing-box 规则集 source（JSON，version 1–5） | <https://sing-box.sagernet.org/configuration/rule-set/source-format/> |
| `adguard` | AdGuard DNS 过滤语法 | <https://adguard-dns.io/kb/general/dns-filtering-syntax/> |
| `hosts` | hosts 文件 | <https://man7.org/linux/man-pages/man5/hosts.5.html> |
| `dnsmasq` | dnsmasq 配置中的域名指令 | <https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html> |
| `wei` | 本项目的手写语法（裸域名带子域） | 本文 §2 |

**不支持**：Quantumult X（只有示例配置，无正式语法文档）、Shadowrocket、Adblock Plus 元素隐藏规则、任何二进制格式（`.mrs`、`.srs`、`.dat`）。指定或识别为这些格式时，该来源报错，在 `check` 阶段即可发现。

### 3.2 `format=auto` 的识别顺序

按内容识别，URL 扩展名和 Content-Type 只作提示。命中第一条即确定；若内容同时满足多种解释，报错要求显式指定。

1. 以 `{` 开头且是含 `version` 与 `rules` 的 JSON → `singbox`
2. YAML 映射且有 `payload:` 键 → `mihomo`（behavior 见 §3.3）
3. 存在 `server=/`、`local=/`、`address=/`、`ipset=/`、`nftset=/` 行 → `dnsmasq`
4. 存在 `||…^`、`|…^`、`@@` 或 `!` 注释行 → `adguard`
5. 首列是 IP、其后是主机名的行占多数 → `hosts`
6. 存在 `TYPE,值` 形式的规则行 → 规则列表（Surge/Loon/Mihomo text 的共同形态，见 §3.4）
7. 纯域名行：
   - 有 `+.` 前缀 → Mihomo domain text
   - 有 `.` 前缀但没有 `+.` → **报错**：Surge DOMAIN-SET 中 `.x` 含自身，Mihomo 中 `.x` 不含自身，必须指定 `surge-domainset` 或 `domain`
   - 只有裸域名 → 精确域名列表（Mihomo text、Surge DOMAIN-SET、AdGuard 纯域名行对裸域名的解释一致：仅自身）

| 输入内容 | 识别结果 | 原因 |
| --- | --- | --- |
| `payload:` + `- '+.a.com'` | mihomo / domain | YAML 有 payload |
| `DOMAIN-SUFFIX,a.com` 等多行 | 规则列表 | `TYPE,值` 形态 |
| `.a.com`、`b.com` 混合，无 `+.` | 报错，要求指定格式 | 前导点在 Surge/Mihomo 含义不同 |
| `a.com`、`b.com` | 精确域名 | 各官方格式一致 |
| HTML 页面 | 来源失败 | 不是规则（见 §8） |

### 3.3 Mihomo rule-provider（yaml/text）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| domain behavior：`+.a.com` | `+.a.com` | 原样 |
| domain behavior：`.a.com` | `.a.com` | Mihomo 中仅子域 |
| domain behavior：`a.com` | `a.com` | 精确 |
| domain behavior：`*.a.com` | `*.a.com` | 一级通配 |
| domain behavior：`a.com/path` | 跳过 | 内核拒绝含 `/` 的条目 |
| ipcidr behavior：`1.2.3.4` | `1.2.3.4/32` | 单 IP 补掩码 |
| ipcidr behavior：`1.2.3.5/24` | `1.2.3.0/24` | 主机位规范化，记录 |
| classical behavior：`DOMAIN-SUFFIX,a.com` | domain：`+.a.com` | 能进集合的进集合 |
| classical behavior：`IP-CIDR,1.0.0.0/8` | ipcidr：`1.0.0.0/8` | 同上 |
| classical behavior：`GEOIP,CN` | classical：`GEOIP,CN,no-resolve` | 上游 IP 条件加 no-resolve |
| classical behavior：`MATCH` / `RULE-SET,x` / `SUB-RULE,…` | 跳过 | 控制与引用语句不能作为成员 |

YAML 用安全解析：拒绝重复键、锚点/别名、自定义 tag、多文档；`payload` 必须是字符串序列。允许文件开头的 `---`。

behavior 自动判断：`payload` 全是 `TYPE,值` → classical；全是地址/网段 → ipcidr；全是原生域名模式 → domain。域名与地址混杂时，地址分入 ipcidr、域名分入 domain，并在说明中提示。

### 3.4 规则列表（Surge / Loon / Mihomo text classical）

三者的行形态都是 `TYPE,值[,策略][,参数…]`。v2 **只保留类型和值**，按类型的字段结构剥离其余字段：

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `DOMAIN-SUFFIX,a.com,DIRECT` | domain：`+.a.com` | 剥离策略 |
| `DOMAIN-KEYWORD,ads,REJECT` | classical：`DOMAIN-KEYWORD,ads` | 剥离策略（含 REJECT 家族） |
| `DOMAIN,a.com,REJECT-TINYGIF` | domain：`a.com` | 同上 |
| `DOMAIN,a.com,Proxy,extended-matching` | domain：`a.com` | 剥离策略与 Surge 参数 |
| `IP-CIDR,1.1.1.0/24,PROXY,no-resolve` | ipcidr：`1.1.1.0/24` | ipcidr 的 no-resolve 由引用追加 |
| `IP-CIDR6,2001:db8::/32` | ipcidr：`2001:db8::/32` | IPv6 |
| `IP-CIDR,2001:db8::/32` | ipcidr：`2001:db8::/32` | 按地址判断地址族 |
| `IP-CIDR,1.1.1.0/24,src` | classical：`SRC-IP-CIDR,1.1.1.0/24` | Mihomo 的 `src` 参数改变含义为来源地址，不能剥离 |
| `IP-ASN,13335` | classical：`IP-ASN,13335,no-resolve` | 上游 IP 条件加 no-resolve |
| `IP-ASN,AS13335` | classical：`IP-ASN,13335,no-resolve` | Surge 允许 AS 前缀 |
| `GEOIP,US,Proxy,no-resolve` | classical：`GEOIP,US,no-resolve` | 剥离策略，保持 no-resolve |
| `DEST-PORT,443` | classical：`DST-PORT,443` | Surge/Loon 名称映射到 Mihomo |
| `SRC-IP,192.168.1.2` | classical：`SRC-IP-CIDR,192.168.1.2/32` | Surge 名称映射 |
| `PROTOCOL,UDP` | classical：`NETWORK,UDP` | 仅 TCP/UDP 有等价 |
| `PROTOCOL,QUIC` | 跳过 | Mihomo 无等价条件 |
| `USER-AGENT,*Spotify*` | 跳过 | 需要 MITM，Mihomo 不支持 |
| `URL-REGEX,^https?://a\.com/x` | 跳过 | 同上 |
| `SUBNET,…`、`CELLULAR-*`、`DEVICE-NAME`、`MAC-ADDRESS`、`SCRIPT`、`HOSTNAME-TYPE` | 跳过 | Mihomo 无等价条件 |
| `DOMAIN-SET,url` / `RULE-SET,url` | 跳过 | 嵌套引用不自动展开（建议直接引用目标来源） |
| `FINAL,DIRECT` | 跳过 | 兜底语句不是成员 |
| `DOMAIN-SUFFIX,.a.com` | domain：`+.a.com`，警告 | 在 Mihomo classical 中永不命中，作者意图明确，修复并提示 |
| `DOMAIN-KEYWORD,.tmall.com` | classical：`DOMAIN-KEYWORD,.tmall.com` | 关键字是子串，点号合法 |
| `DOMAIN-REGEX,"^a,b\.com$"` | classical：`DOMAIN-REGEX,^a,b\.com$` | Surge 允许用引号包裹含逗号的值 |
| `AND,((DOMAIN,a.com),(NETWORK,UDP)),REJECT` | classical：`AND,((DOMAIN,a.com),(NETWORK,UDP))` | 按括号深度解析，剥离末尾策略 |
| `AND,((IP-CIDR,1.0.0.0/8),(DST-PORT,443))` | classical：`AND,((IP-CIDR,1.0.0.0/8,no-resolve),(DST-PORT,443))` | no-resolve 加在 IP 叶节点 |
| `# 注释`、`// 注释`、`; 注释` | 忽略 | Surge 文档定义的注释 |
| `DOMAIN,a.com // 行尾注释` | domain：`a.com` | Surge 允许行尾注释 |
| 小写类型 `domain-suffix,a.com` | domain：`+.a.com` | 类型名按 ASCII 大写查注册表 |
| `UNKNOWN-TYPE,x` | 跳过 | 未登记类型，说明里写出类型名 |

### 3.5 Surge DOMAIN-SET（`format=surge-domainset`）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `a.com` | `a.com` | 精确 |
| `.a.com` | `+.a.com` | **Surge 中前导点包含自身**（与 Mihomo 相反） |
| `# 注释` / `// 注释` | 忽略 | 官方注释语法 |

### 3.6 sing-box 规则集（`format=singbox`）

一条 headless rule 的含义是：域名/IP 类字段之间是「或」，与其他字段之间是「与」。

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `{"domain": ["a.com"]}` | domain：`a.com` | 精确 |
| `{"domain_suffix": ["a.com"]}` | domain：`+.a.com` | 无点后缀含自身（1.9+ 语义） |
| `{"domain_suffix": [".a.com"]}` | domain：`.a.com` | 带点时仅子域 |
| `{"domain_keyword": ["ads"]}` | classical：`DOMAIN-KEYWORD,ads` | 关键字 |
| `{"domain_regex": ["^a\\.com$"]}` | classical：`DOMAIN-REGEX,^a\.com$` | 正则 |
| `{"ip_cidr": ["1.0.0.0/8"]}` | ipcidr：`1.0.0.0/8` | 目标地址 |
| `{"source_ip_cidr": ["10.0.0.0/8"]}` | classical：`SRC-IP-CIDR,10.0.0.0/8` | 来源地址 |
| `{"domain_suffix": ["a.com"], "port": [443]}` | classical：`AND,((DOMAIN-SUFFIX,a.com),(DST-PORT,443))` | 与关系不能拆成并集 |
| `{"port_range": ["1000:2000"]}` | classical：`DST-PORT,1000-2000` | 区间写法转换 |
| `{"network": "udp"}` | classical：`NETWORK,UDP` | 网络类型 |
| `{"process_name": ["a.exe"]}` | classical：`PROCESS-NAME,a.exe` | 进程 |
| `{"type": "logical", "mode": "or", "rules": […]}` | 展开为各成员（并集） | 顶层 or 等价于多条成员 |
| `{"invert": true, "domain": ["a.com"]}` | classical：`NOT,((DOMAIN,a.com))` | 取反 |
| 含 `wifi_ssid`、`network_type`、`query_type` 等字段的规则 | 整条跳过 | 无等价条件；只删字段会扩大匹配 |
| `.srs` 二进制 | 来源报错 | 二进制格式无官方文档 |

### 3.7 AdGuard DNS 过滤语法（`format=adguard`）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `\|\|a.com^` | `+.a.com` | 域名及全部子域 |
| `\|\|a.com^$important` | `+.a.com` | `important` 只影响优先级，剥离 |
| `\|a.com^` | `a.com` | 锚定整个主机名 |
| `a.com` | `a.com` | 官方：仅该域名，不含子域 |
| `\|\|*.a.com^` | `.a.com` | 仅子域 |
| `0.0.0.0 a.com` | `a.com` | hosts 风格行，仅自身 |
| `@@\|\|a.com^` | 抵消同来源中完全相同的 `\|\|a.com^`；无法精确抵消时跳过并说明 | 例外规则无法用正向集合表达 |
| `\|\|a.com^$badfilter` | 抵消同来源中的 `\|\|a.com^` | 官方定义的禁用规则 |
| `\|\|a.com^$client=…`、`$ctag`、`$dnstype`、`$dnsrewrite`、`$denyallow` | 跳过 | 条件化规则，去掉修饰符会扩大匹配 |
| `\|\|a.com^$unknownmod` | 跳过 | 官方：含未列出修饰符的整条忽略 |
| `/ads[0-9]+\.com/` | 跳过 | AdGuard 正则方言与 Mihomo regexp2 不保证一致 |
| `\|\|ad*.a.com^` | 跳过 | 局部通配无法用原生模式等价表达 |
| `\|\|1.2.3.4^` | 跳过 | IP 模式在 DNS 过滤中的含义不同于目标地址规则 |
| `! 注释`、`# 注释` | 忽略 | 官方注释语法 |

### 3.8 hosts（`format=hosts`）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `0.0.0.0 a.com` | `a.com` | 每个主机名是精确条目，IP 列忽略 |
| `127.0.0.1 a.com b.com` | `a.com`、`b.com` | 别名也是精确条目 |
| `127.0.0.1 localhost`、`::1 ip6-localhost` | 忽略 | 本机名，不是分流目标 |
| `0.0.0.0 0.0.0.0` | 忽略 | 主机名列不是域名 |
| `a.com # 注释` | 忽略 `#` 后内容 | 官方注释语法 |

忽略的本机名：`localhost`、`localhost.localdomain`、`local`、`broadcasthost`、`ip6-localhost`、`ip6-loopback`、`ip6-localnet`、`ip6-mcastprefix`、`ip6-allnodes`、`ip6-allrouters`、`ip6-allhosts`。

### 3.9 dnsmasq（`format=dnsmasq`）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `server=/a.com/114.114.114.114` | `+.a.com` | 官方：按完整标签匹配域名及子域 |
| `server=/a.com/b.com/1.1.1.1` | `+.a.com`、`+.b.com` | 一行多个域名 |
| `address=/a.com/0.0.0.0`、`local=/a.com/` | `+.a.com` | 同一域名语法 |
| `ipset=/a.com/set1`、`nftset=/a.com/4#inet#t#s` | `+.a.com` | 同一域名语法，剥离集合名 |
| `server=/*.a.com/1.1.1.1` | `.a.com` | 官方：仅子域 |
| `server=/#/1.1.1.1` | 跳过 | 匹配全部域名 |
| `server=//1.1.1.1` | 跳过 | 仅匹配无点主机名 |
| `server=1.1.1.1`、`cache-size=…` | 忽略 | 不含域名的配置项 |

## 4. 域名规范化（全部来源）

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `A.Com` | `a.com` | 内核不区分 ASCII 大小写 |
| `a.com.` | `a.com` | 内核拒绝末尾点，修复并记录 |
| `例子.com` | `xn--fsqu00a.com` | 统一 A-label，否则永远不会命中 |
| `_dmarc.a.com` | `_dmarc.a.com` | 下划线合法，保留 |
| `local`、`home.arpa` | 保留 | 路由列表不按公共后缀表校验 |
| `a..com`、`-a.com`、超长标签 | 跳过 | 非法域名 |
| `1.2.3.4`（出现在域名列表中） | ipcidr：`1.2.3.4/32`，提示 | IP 字面量在 domain 集合中永不命中 |
| `www.a.com` | `www.a.com` | 不像广告列表那样去掉 `www.` 扩大范围 |

## 5. domain 集合的去重与合并

内部用反向标签 trie，每个节点区分三种状态：EXACT（仅自身）、SUBONLY（仅子域）、SUFFIX（自身 + 子域）。通配模式用「标签数区间 + 右端固定标签」精确判断包含（规范 1.5 第 9.3 节）。

| 同一合集中的输入 | 输出 | 原因 |
| --- | --- | --- |
| `+.a.com`、`www.a.com` | `+.a.com` | 后缀覆盖子域精确条目 |
| `+.a.com`、`+.b.a.com` | `+.a.com` | 后缀覆盖子后缀 |
| `+.a.com`、`a.com` | `+.a.com` | 后缀覆盖自身 |
| `.a.com`、`a.com` | `+.a.com` | 仅子域 + 自身 = 后缀 |
| `.a.com`、`x.a.com` | `.a.com` | 仅子域覆盖其下条目 |
| `a.com`、`x.a.com` | `a.com`、`x.a.com` | 精确父域不覆盖子域 |
| `+.a.com`、`not-a.com` | 两者都保留 | 按完整标签判断 |
| `x.a.com`、`y.a.com`、`z.a.com` | 原样保留三条 | 有限个子域不推断为通配 |
| `*.a.com`、`x.a.com` | `*.a.com` | 一级通配覆盖一级子域 |
| `*.a.com`、`x.y.a.com` | 两者都保留 | 一级通配不覆盖二级 |
| `*.a.com`、`a.com` | 两者都保留 | 一级通配不含自身 |
| `.a.com`、`*.a.com` | `.a.com` | 仅子域覆盖一级通配 |
| `a.*.com`、`a.b.com` | `a.*.com` | 中间通配覆盖对应位置 |
| `a.*.com`、`b.a.com` | 两者都保留 | 固定标签位置不同 |
| `xbox.*.a.com`、`.xbox.*.a.com` | `+.xbox.*.a.com` | 自身 + 全部子域合成后缀 |
| `+.a.com` 重复 3 次 | `+.a.com` | 至少保留一个代表 |

去重只在同一合集（或合并后的同一组文件）内进行；不同合集即使重叠也各自完整，跨合集的遮挡只写进分析报告。

## 6. ipcidr 集合的合并

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `10.0.0.0/8`、`10.1.0.0/16`、`10.1.2.3/32` | `10.0.0.0/8` | 大网段包含小网段与单 IP |
| `192.0.2.0/25`、`192.0.2.128/25` | `192.0.2.0/24` | 相邻且对齐，精确合成 |
| `192.0.2.0/26`、`192.0.2.128/26` | 两者都保留 | 中间有空洞，不能填补 |
| `192.0.2.1`、`192.0.2.3` | `192.0.2.1/32`、`192.0.2.3/32` | 不连续地址不提升为网段 |
| `192.0.2.0/25`、`192.0.2.128/26` | 两者都保留 | 合并后不是单个对齐网段时，输出精确覆盖的网段组合 |
| `0.0.0.0/0`、`1.2.3.4` | `0.0.0.0/0` | 全地址空间，无整数溢出 |
| `::ffff:1.2.3.4` | `1.2.3.4/32` | IPv4 映射地址还原为 IPv4 |
| `::fffe:0:0/95` | `::fffe:0:0/95` | 包含整个映射段的更大前缀仍是 IPv6 网段，不跨地址族折叠 |
| `fe80::1%eth0` | 跳过 | zone ID 不是目标地址 |
| `10.0.0.0/8`、`2001:db8::/32` | 两者分别保留 | IPv4/IPv6 分别处理 |
| `1.2.3.0/33` | 跳过 | 非法前缀不修剪成其他地址 |

## 7. classical 的去重与跨类型关系

去重之前，上游中范围过宽的规则（如 `DOMAIN-KEYWORD,ads`）已被过滤，见 [broad-rules](broad-rules.md)。下表的输入都是过滤后仍保留的规则。

| 同一合集中的输入 | 输出 | 原因 |
| --- | --- | --- |
| `DOMAIN-KEYWORD,ads` 出现两次 | 一条 | 规范化文本相同 |
| `DOMAIN-KEYWORD,ads`、`DOMAIN-KEYWORD,ADS` | 一条 | 关键字大小写不敏感（内核小写比较） |
| `PROCESS-NAME,A.exe`、`PROCESS-NAME,a.exe` | 两条 | 进程名按平台语义，不全局小写 |
| `DOMAIN-KEYWORD,google` 与 domain `+.google.com` | 两者都保留 | 删掉域名会让命中从 trie 退回线性关键字比对，变慢（与 SukkaW/Surge 的取舍不同） |
| `DOMAIN-REGEX,^.*\.a\.com$` 与 domain `x.a.com` | 两者都保留 | 正则的覆盖关系不作为删除依据 |
| `DST-PORT,80`、`DST-PORT,81`、`DST-PORT,82` | `DST-PORT,80-82` | 同字段端口区间精确合并 |
| `DST-PORT,80`、`SRC-PORT,80` | 两者都保留 | 方向不同 |
| `AND,((DOMAIN,a.com),(NETWORK,UDP))` 重复 | 一条 | 树结构相同 |
| `AND,((NETWORK,UDP),(DOMAIN,a.com))` 与上一条 | 两者都保留 | 不对逻辑表达式做交换律化简 |

## 8. 来源失败与异常

| 情况 | 处理 |
| --- | --- |
| HTTP 非 2xx、超时、连接失败 | 本次使用该来源上次成功的副本，说明中告警 |
| 返回 HTML 页面 | 同上 |
| 空响应 | 同上 |
| 无法识别的格式、解析错误比例超过阈值 | 同上 |
| 条目数比上次成功少 50% 以上 | 同上（疑似上游异常） |
| 连续失败超过 7 天 | 继续使用旧副本，说明顶部提示「该来源可能已失效，建议从 my.wei 删除」 |
| 首次添加即失败（没有任何旧副本） | 本次构建失败，保留上一版发布 |
| HTTP 304 | 仅当本地已有哈希一致的对象时复用 |

## 9. 输出规划

| 情况 | 输出 |
| --- | --- |
| 合集只有域名 | 仅 `clash-domain/X.yaml` |
| 合集只有网段 | 仅 `clash-ipcidr/X-ipcidr.yaml` |
| 合集三类都有 | 三个文件，在 `rulesets.toml` 中按 domain → ipcidr → classical 连续排列 |
| 某类为空 | 不生成该文件，也不生成对应条目 |
| `[Rules]` 中 `A: G`、`B: G` 相邻 | 合并为一组文件 `A__B`，内容为两者并集 |
| `A: G`、`X: H`、`B: G` | 不合并（中间有其他规则） |
| 同一合集被引用两次（不相邻） | 共用同一组文件，`rulesets.toml` 出现两次 |
| 内联 `GEOIP,CN: DIRECT` | `ruleset = "[]GEOIP,CN"`，按原样不加参数 |
| 内联 `GEOIP,JP: 🌺 日本专线,no-resolve` | `ruleset = "[]GEOIP,JP,no-resolve"` |
| 内联 `DOMAIN-REGEX,…` 或 `AND,…` | 报错：subconverter 会用正则重排含逗号的内联规则，导致损坏 |
| 内联 `MATCH: G` | `ruleset = "[]MATCH"`，必须是最后一条 |
| 被引用但所有来源都为空的合集 | 报错，除非配置中允许该合集为空 |
| 文件名与其他 provider 名冲突（按 subconverter 的 `findFileName` 规则） | 换用带行为后缀和哈希的安全文件名 |
| `rulesets.toml` 条目超过 64 | 提示（subconverter 外部配置的上限），不报错 |

依据：angwz/subconverter `a33d49e` 的 `src/generator/template/templates.cpp` 与 `src/config/binding.h`。

## 10. 规则文件的排列与文件头

domain 文件按覆盖范围从宽到窄排列。组内先比较写出的标签数（少的在前），再按字母序：

| 次序 | 写法 | 例子 |
| --- | --- | --- |
| 1 | `+.x`：自身及全部子域 | `+.us` → `+.01.org` → `+.academic.eb.com` |
| 2 | `.x`：仅子域 | `.cdn.example.org` |
| 3 | 含 `*` 的定长通配 | `*.example.com`、`a.*.example.com` |
| 4 | 精确主机名 | `adobeereg.com` → `amp.akamaized.net` |

这个次序不影响匹配速度：Mihomo 的 `NewDomainSet`（`component/trie/domain_set.go`）会收集全部条目，用 `sort.Strings` 排序后再建 trie。ipcidr 文件按地址升序排列，IPv4 在前、IPv6 在后。classical 文件按 §1 的成本次序排列，同类型相邻，类型之间空一行。

文件头是 `# KEY: value` 形式的整行注释，Mihomo 逐行解析时跳过（`rules/provider/provider.go` 的 `rulesParse`）：

```yaml
# NAME: China
# GROUP: DIRECT
# REPO: https://github.com/angwz/domainrouter_v2
# UPDATED: 2026-11-09 04:17:49 (UTC+8)
# TYPE: ipcidr
# TOTAL: 12569
# IP-CIDR: 8289
# IP-CIDR6: 4280
payload:
```

| 字段 | 含义 |
| --- | --- |
| `NAME` | 合集名；相邻同目标合并的块写作 `A + B` |
| `GROUP` | 引用该文件的策略组 |
| `REPO` | 发布地址为 `raw.githubusercontent.com` 时由 `output.base_url` 推出；其他地址省略 |
| `UPDATED` | 该文件内容最后一次变化的时间，发布时写入（见下） |
| `TYPE`、`TOTAL` | 行为与条目数；ipcidr 与 classical 含多种类型时，按类型分列条目数 |

文件头之后是来源图例：本文件实际出现的来源按 my.wei 中的声明顺序编为 A、B、C……，名称为「作者或主机名 · 最后两级路径」，简称重复时写完整 URL。

```yaml
# SOURCE A: my.wei
# SOURCE B: blackmatrix7 · USMedia/USMedia.list
# SOURCE C: MetaCubeX · geosite/category-dev.yaml
payload:
  - '+.us'                     # A  覆盖 +.hulu.us B, +.intel.us I J 等 3 条
  - '+.01.org'                 # C I J
  - '178.236.232.0/23'         # 合并 178.236.232.0/24 A B E, 178.236.233.0/24 F
```

每条规则的同行注释最多三段：

| 段 | 含义 |
| --- | --- |
| 字母 | 这条规则原样出现在哪些来源中 |
| `合并 …` | 它由哪些输入合成（本身不在任何来源中原样出现），最多列 3 条 |
| `覆盖 …` | 被它完整包含而删去的输入及其来源，最多列 2 条，超出写「等 N 条」 |

与输出同类型的 classical 输入只写载荷，例如 `DOMAIN-KEYWORD,openai` 后写 `覆盖 openaicom-api B`。注释从同一列开始：取本文件 90% 条目都能放下的宽度（不超过 56 列），更长的条目只隔两个空格。

完整来历用 `domainrouter_v2 explain --rule '+.us'` 查看，列出全部被合并、被覆盖的输入和来源的完整 URL。来源标注由 `provenance.py` 独立计算：对每条输入找出完整包含它的那条输出，不只依赖优化过程的记录；找不到时构建给出 `W_TRACE_GAP` 警告，说明合并算法可能有误。

同行注释与 `payload:` 一起交给 YAML 解析器，解析器忽略注释，Mihomo 加载的条目数不变（内核层验证核对）。代价是文件体积，实测见 [performance](../performance.md)。

`build` 的产物不含 `UPDATED`，所以两次构建逐字节相同。发布时，内容（除 `UPDATED` 行外，含来源标注）与已发布版本相同的文件保留原字节和原时间，只有变化的文件写入新时间。这样每次提交只改动真正变化的文件，客户端也不会因为时间戳变化而重新下载。
