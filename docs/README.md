# 文档地图

按你想做的事找到对应的文档。每份文档只负责一个主题，同一事实只在一处详述，其余位置用链接指过去。

## 使用

| 文档 | 读完你会知道 |
| --- | --- |
| [guide/my-wei.md](guide/my-wei.md) | 怎样写 `my.wei`：合集、域名语义、上游来源、`[Rules]` |
| [guide/configuration.md](guide/configuration.md) | `config/domainrouter_v2.toml` 的每个字段与目录约定 |
| [guide/subconverter.md](guide/subconverter.md) | 产物如何被 subconverter 引用，以及它的限制 |
| [guide/daily-automation.md](guide/daily-automation.md) | 每日工作流做什么、怎样启用、怎样回滚与排障 |

## 规则语义

| 文档 | 内容 |
| --- | --- |
| [rules/merge-cases.md](rules/merge-cases.md) | 各来源格式的转换、去重与合并、输出规划、文件排列与来源标注，每个案例都有测试 |
| [rules/broad-rules.md](rules/broad-rules.md) | 哪些上游规则因范围过宽被过滤、哪些列入清单提醒，以及判定依据 |

## 设计

| 文档 | 内容 |
| --- | --- |
| [design/architecture.md](design/architecture.md) | 管线、模块职责与依赖方向、关键算法、三层验证 |
| [design/performance.md](design/performance.md) | 实测性能与优化效果 |
| [decisions/](decisions/) | 影响架构或兼容性的决定，按编号递增；与其他文档冲突时以决定为准 |

## 开发

| 文档 | 内容 |
| --- | --- |
| [development/progress.md](development/progress.md) | 当前进度、最近一次验证、下一步 |
| [development/feedback.md](development/feedback.md) | 维护者提出的每条意见及其处理结果 |

## 历史

| 文档 | 内容 |
| --- | --- |
| [history/v1-migration.md](history/v1-migration.md) | 从 v1 迁移时的输入来源、预览结果与行为差异 |
| [history/spec-1.5/](history/spec-1.5/) | 项目起步时交给编码代理的实施规范（归档，不再更新） |

## 给 AI 代理

先读仓库根目录的 [CLAUDE.md](../CLAUDE.md)，再按其中的顺序阅读。约定：

- **状态**以 `development/progress.md` 为准，**语义**以 `rules/merge-cases.md` 为准，**取舍**以 `decisions/` 为准。
- 维护者的新意见追加到 `development/feedback.md`，只写中性的总结，不引用原话。
- 文档中的命令、路径、配置键必须与代码一致；性能数字只写实测值。
