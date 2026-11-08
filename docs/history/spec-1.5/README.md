# 实施规范 1.5（归档）

DomainRouter v2 的起点是一份写给 AI 编码代理的实施规范，而不是一份代码。本目录原样保存这份规范，用来回答“当初为什么这样设计”。

| 文件 | 内容 |
| --- | --- |
| [index.md](index.md) | 规范入口与阅读顺序 |
| [01-foundations-and-input.md](01-foundations-and-input.md) | 基础约定、输入语义、来源与快照 |
| [02-engine-and-algorithms.md](02-engine-and-algorithms.md) | 数据模型、通配包含、去重合并、分区与排序 |
| [03-artifacts-and-verification.md](03-artifacts-and-verification.md) | 产物、兼容性、验证与命令契约 |
| [04-delivery-and-handoff.md](04-delivery-and-handoff.md) | 每日生成、开源交付与里程碑 |
| [start-prompt.md](start-prompt.md) | 交给编码代理的启动提示 |

## 阅读时请注意

- **它不是现状。** 实施过程中有若干条款被调整，例如只输出 YAML、不生成 base 配置、上游每日跟随更新、过滤过宽的上游规则。调整记录在 [decisions/](../../decisions/)，与本规范冲突时以决定为准。
- **路径是归档前的。** 规范写于项目尚无代码时，文中的 `docs/v2-implementation-spec.md`、`docs/v2/…` 现在位于本目录；除修正文件间的相对链接外，内容未作改动。
- **当前行为以活文档为准。** 见 [文档地图](../../README.md)。
