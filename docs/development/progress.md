# 实施进度

> 唯一状态记录。区分「已实现」与「已验证」；过期内容直接覆盖。

## 当前

- 里程碑：**S0 → M1**
- 正在做：M1 解析与模型（诊断、规则类型注册表、域名/IP 模型、`my.wei` 解析、来源格式适配器、参考解释器）。

## 已完成

| 内容 | 位置 | 状态 |
| --- | --- | --- |
| 规范与旧资料调研、用户决定 | [decisions/0001](../decisions/0001-deviations-from-spec-1.5.md) | 已采纳 |
| 转换与合并语义契约 | [rules/merge-cases.md](../rules/merge-cases.md) | 已编写，待用户审阅；测试未实现 |
| 工程骨架（uv、Python 3.13.18、依赖锁） | `pyproject.toml`、`uv.lock` | 已实现：`uv sync` 成功 |

## 最近验证

- 2026-11-08 · Windows 10 x64 · `uv sync`：成功，`import domainrouter_v2` 正常。

## 已知问题与待核验

- 许可证未选定（首次公开发布前决定）。
- 外部配置 `rulesets` 上限 64 条（subconverter `settings.h`），只作提示。
- Mihomo 逻辑规则子条件中 `no-resolve` 的解析需在 M3 内核层确认。

## 下一步

1. 实现 `diagnostics`、`registry`、`model.domain`、`model.ip` 及其测试。
2. 实现 `my.wei` 词法与 `[Rules]` 解析（规范 §4）。
3. 实现各来源格式适配器，按 merge-cases §3 编写测试。
