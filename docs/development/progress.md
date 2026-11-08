# 实施进度

> 唯一状态记录。区分「已实现」与「已验证」；过期内容直接覆盖。

## 当前

- 里程碑：**M1–M4a 完成**，等待用户审阅；M4b（远端、发布、许可）未开始，需要用户授权。
- 每日流程状态：**已实现并本地演练通过；远端定时与发布均未启用**（远端仓库尚未创建）。

## 已完成

| 内容 | 位置 | 已实现 | 已验证 |
| --- | --- | --- | --- |
| 决策与语义契约 | [decisions/0001](../decisions/0001-deviations-from-spec-1.5.md)、[merge-cases](../rules/merge-cases.md) | ✓ | 案例均有单元测试 |
| 域名模式、包含判定、网段合并 | `model/` | ✓ | 穷举交叉校验 + 属性测试 |
| 规则行转换、类型注册表、来源格式与自动识别 | `parse/`、`registry.py` | ✓ | 单元测试；真实 210 来源 0 失败 0 跳过 |
| my.wei 解析 | `parse/document.py`、`parse/freeline.py` | ✓ | 单元测试；v1 my.wei 0 错误 |
| 优化与规划 | `optimize/`、`planner.py` | ✓ | 属性测试；真实数据语义层 + 内核层 0 不一致 |
| 来源获取、快照、Happy Eyeballs | `sources/` | ✓ | 伪造传输测试；真实网络 |
| 构建、输出、更新说明、发布暂存 | `build.py`、`emit.py`、`report.py`、`publish.py` | ✓ | 端到端测试；逐字节可重建 |
| 验证（语义层、内核层）、explain | `verify/`、`explain.py`、`tools/kernel-adapter/` | ✓ | Mihomo v1.19.33 实测 |
| 工具锁与准备 | `tools.py`、`tools.lock.json` | ✓ | 下载并校验 SHA-256 |
| 每日工作流、CI | `.github/workflows/`、`scripts/` | ✓ | 本地演练 6 场景通过；**未在 GitHub 上运行** |
| 文档、开源资料、安装包 | `README.md`、`docs/`、`CONTRIBUTING.md` 等 | ✓ | 链接检查；wheel 仓库外安装运行 |

## 最近验证（2026-11-08 · Windows 10 x64 · Python 3.13.18 · uv 0.13.6）

- `pytest`：337 passed（含 kernel 标记）；`ruff check`、`ruff format --check`、`mypy --strict`：通过。
- 真实 profile：`fetch` 冷启动 29 s / 已有快照 6 s；`build` 18.5 s；两次构建逐字节一致；`verify --level kernel` 0 不一致、59 个 provider 条目数与 Mihomo 加载数一致。
- `scripts/rehearse-daily.sh`：6 个场景全部通过（语义层验证模式）。
- `uv build`：wheel 只含包代码与工具锁；在仓库外全新 venv 中安装，示例 check/build/verify/explain 通过。
- 性能数据见 [performance.md](../performance.md)。

## 已知问题与待核验

- `rulesets.toml` 66 条，超过 subconverter 外部配置的 64 条上限（只告警；需用户确认加载方式）。
- v1 的 `release` 分支已被清空（提交 `0addd6f`），用户若仍引用 v1 地址可能取不到规则。
- subconverter 行为依据 fork 源码模拟，未在 VPS 实际运行；Linux 上的测试与性能需远端 CI 启用后补充。
- 许可证未选定。

## 下一步（需用户决定）

1. 审阅 merge-cases、迁移报告与更新说明样例，确认语义。
2. M4b：选定许可证、创建远端仓库、手动运行一次每日工作流、设置 `PUBLISH_ENABLED`、切换 subconverter 引用（见 [daily-automation](../daily-automation.md)）。
3. 可选：MRS 输出（需 subconverter 写出 `format`）、Web、AI 建议。
