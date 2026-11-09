# 0003 · 同时发布 MRS

- 状态：已采纳（2026-11-09，维护者提出）
- 取代：[0001](0001-deviations-from-spec-1.5.md) #1 中「MRS 推迟」的部分；YAML 仍是主格式

## 背景

[0001](0001-deviations-from-spec-1.5.md) 推迟了 MRS，因为维护者使用的 subconverter fork 不会为 provider 写出 `format`，引用 MRS 需要改动服务端。规则公开之后，读者不只是维护者本人：直接写 Mihomo 配置、只挑几个规则集的人，可以自己写 `format: mrs`。

MRS 与 YAML 在内核中是同一个数据结构，匹配速度相同，区别在于加载。实测加载全部 provider，YAML 约 3.8 s，MRS 约 0.8 s；体积也只有约七分之一。

## 决定

1. 配置项 `output.mrs = true` 时，每个 domain 与 ipcidr 文件旁边再发布一个同名的 `.mrs` 文件，与 YAML 同目录。classical 没有 MRS 形式。
2. 编码交给固定版本 Mihomo 自带的 `convert-ruleset`，输入就是刚生成的 YAML；不在 Python 中重新实现 MRS。
3. `rulesets.toml` 继续引用 YAML，维护者的 subconverter 接入方式不变。
4. 内核层验证增加 MRS 变体：同一张规则表改为从 MRS 加载 domain 与 ipcidr，命中结果和加载条目数必须与 YAML 完全一致。

## 取舍

- **依赖 Mihomo 二进制**：开启 MRS 后，构建需要先运行 `tools prepare`。每日流程本来就为内核层验证准备了它；`output.mrs` 默认关闭，fork 的人不受影响。
- **确定性**：同一 YAML 两次编译的 MRS 逐字节相同，内容不变时不会产生提交。
- **不加注释**：MRS 是二进制格式，不可阅读；来历与注释只保留在 YAML 中。
