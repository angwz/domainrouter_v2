# 实施进度

> 唯一状态记录。区分「已实现」与「已验证」；过期内容直接覆盖。

## 当前

- 里程碑：**M1–M4a 完成**；M4a 之后按用户反馈新增宽泛规则过滤与清单、规则文件头注释（[decisions/0002](../decisions/0002-filter-broad-upstream-rules.md)）。M4b（远端、发布、许可）未开始，需要用户授权。
- 每日流程状态：**已实现并本地演练通过；远端定时与发布均未启用**（远端仓库尚未创建）。

## 已完成

| 内容 | 位置 | 已实现 | 已验证 |
| --- | --- | --- | --- |
| 决策与语义契约 | [decisions/0001](../decisions/0001-deviations-from-spec-1.5.md)、[merge-cases](../rules/merge-cases.md) | ✓ | 案例均有单元测试 |
| 域名模式、包含判定、网段合并 | `model/` | ✓ | 穷举交叉校验 + 属性测试 |
| 规则行转换、类型注册表、来源格式与自动识别 | `parse/`、`registry.py` | ✓ | 单元测试；真实 210 来源 0 失败 0 跳过 |
| my.wei 解析 | `parse/document.py`、`parse/freeline.py` | ✓ | 单元测试；v1 my.wei 0 错误 |
| 优化与规划 | `optimize/`、`planner.py` | ✓ | 属性测试；真实数据语义层 + 内核层 0 不一致 |
| 宽泛规则判定、上游过滤、清单 | `breadth.py`、`data/`、[broad-rules](../rules/broad-rules.md) | ✓ | 案例测试；真实数据过滤 0 条、列出宽泛规则 554 条 |
| 来源获取、快照、Happy Eyeballs | `sources/` | ✓ | 伪造传输测试；真实网络 |
| 构建、输出（含文件头注释）、更新说明、发布暂存 | `build.py`、`emit.py`、`report.py`、`publish.py` | ✓ | 端到端测试；逐字节可重建；带注释的文件经 Mihomo 加载条目数一致 |
| 验证（语义层、内核层）、explain | `verify/`、`explain.py`、`tools/kernel-adapter/` | ✓ | Mihomo v1.19.33 实测 |
| 工具锁与准备 | `tools.py`、`tools.lock.json` | ✓ | 下载并校验 SHA-256 |
| 每日工作流、CI | `.github/workflows/`、`scripts/` | ✓ | 本地演练 6 场景通过；**未在 GitHub 上运行** |
| 文档、开源资料、安装包 | `README.md`、`docs/`、`CONTRIBUTING.md` 等 | ✓ | 链接检查；wheel 仓库外安装运行 |

## 最近验证（2026-11-08 · Windows 10 x64 · Python 3.13.18 · uv 0.13.6）

- `pytest`：405 passed（含 kernel 标记）；`ruff check`、`ruff format --check`、`mypy --strict`：通过。
- 真实 profile：`build` 约 19.5 s（宽泛规则判定约增加 1.5 s）；两次构建逐字节一致；`verify` 语义层 0 不一致；`verify --level kernel` 0 不一致（50,004 个请求），59 个带注释头的 provider 条目数与 Mihomo 加载数一致。
- `scripts/rehearse-daily.sh`：6 个场景全部通过（语义层验证模式）。
- `uv build`：wheel 含包代码、工具锁与 `data/` 下两份数据文件；测试在仓库外安装运行。
- 性能数据见 [performance.md](../performance.md)。

## 已知问题与待核验

- `rulesets.toml` 66 条，超过 subconverter 外部配置的 64 条上限：用户确认不影响其使用方式，保留提示。
- subconverter 行为依据 fork 源码模拟，未在 VPS 实际运行；Linux 上的测试与性能需远端 CI 启用后补充。
- 宽泛关键词表需随使用补充；DOMAIN-REGEX 的“匹配一切”用 Python `re` 近似判断。
- 许可证未选定。

## 下一步（需用户决定）

1. 审阅 merge-cases、[broad-rules](../rules/broad-rules.md) 与真实数据的宽泛规则清单，确认判定标准。
2. M4b：选定许可证、创建远端仓库、手动运行一次每日工作流、设置 `PUBLISH_ENABLED`、切换 subconverter 引用（见 [daily-automation](../daily-automation.md)）。
3. 可选：MRS 输出（需 subconverter 写出 `format`）、Web、AI 建议。
