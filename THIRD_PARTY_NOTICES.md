# 第三方组件与数据来源

本项目自身的代码许可尚未选定（见 [README](README.md#许可)）。下列第三方内容各自适用其原有许可，不因被本项目调用、下载或转换而改变许可。

## Python 运行依赖（随 wheel 安装，不随仓库分发）

| 包 | 用途 | 许可 |
| --- | --- | --- |
| httpx | 下载上游来源 | BSD-3-Clause |
| httpcore | httpx 的连接层（自定义 Happy Eyeballs 后端） | BSD-3-Clause |
| idna | 国际化域名转换（UTS #46） | BSD-3-Clause |
| PyYAML | 读取 YAML 来源 | MIT |
| tomli-w | 写出 TOML | MIT |

开发依赖（pytest、hypothesis、ruff、mypy 等）只用于测试，不随安装包分发。完整版本见 `uv.lock`。

## 验证工具（`tools prepare` 按需下载，不随仓库或安装包分发）

| 工具 | 版本 | 用途 | 许可 |
| --- | --- | --- | --- |
| Mihomo | v1.19.33 | 内核层验证 | GPL-3.0 |
| Go 工具链 | 1.26.9 | 编译验证适配器 | BSD-3-Clause |
| Mihomo Go 模块及其依赖 | v1.19.33 | 验证适配器（`tools/kernel-adapter`，只在本地编译运行） | GPL-3.0 及各依赖的许可 |
| geoip.metadb、geosite.dat | MetaCubeX/meta-rules-dat@d5574ea | 内核层验证中的 GEOIP/GEOSITE 条件 | 见 meta-rules-dat 仓库 |
| GeoLite2-ASN.mmdb | 同上（MaxMind 数据） | 内核层验证中的 IP-ASN 条件 | CC BY-SA 4.0，受 MaxMind GeoLite2 EULA 约束 |

下载地址与 SHA-256 见 [`src/domainrouter_v2/tools.lock.json`](src/domainrouter_v2/tools.lock.json)。

`tools/kernel-adapter` 链接了 GPL-3.0 的 Mihomo 代码。它只作为本地测试工具编译运行，不对外分发二进制；如果将来分发其二进制，需要满足 GPL-3.0 的要求。

## 规则数据

本项目不内置任何第三方规则数据。`my.wei` 引用的上游（例如 blackmatrix7/ios_rule_script、MetaCubeX/meta-rules-dat、ruleset.skk.moe）在运行时下载，各自适用其作者的许可与使用条款。`release` 分支发布的规则文件由这些数据转换、合并而来，再分发时请遵守相应上游的条款。

`state` 分支保存的是规范化后的成员，不是上游原文，但仍源自上游数据，同样适用上述说明。

## 参考实现

格式语义来自各工具的官方文档：Mihomo、Surge、Loon、sing-box、AdGuard DNS、hosts(5)、dnsmasq(8)。subconverter 的行为模拟依据 angwz/subconverter@a33d49e 的源码（GPL-3.0），本项目没有复制其代码。
