# 进度

> 项目的唯一状态记录。区分「已实现」与「已验证」，过期内容直接覆盖，不保留流水账。

## 现在

- **阶段**：核心功能完成，准备首次发布到 GitHub。远端仓库、定时运行与发布尚未启用。
- **最近的改动**：宽泛规则过滤与清单（[0002](../decisions/0002-filter-broad-upstream-rules.md)）、v1 风格的文件头与从宽到窄的排列、逐条来源标注与 `explain --rule`、文档重组为 guide / rules / design / development / history。

## 能力一览

| 能力 | 位置 | 已实现 | 已验证 |
| --- | --- | :---: | --- |
| 域名模式、包含判定、网段合并 | `model/` | ✓ | 穷举交叉校验与属性测试 |
| 规则行转换、类型注册表、来源格式与自动识别 | `parse/`、`registry.py` | ✓ | 单元测试；真实 210 个来源 0 失败 0 跳过 |
| my.wei 解析 | `parse/document.py`、`parse/freeline.py` | ✓ | 单元测试；v1 my.wei 0 错误 |
| 优化与规划 | `optimize/`、`planner.py` | ✓ | 属性测试；真实数据语义层与内核层 0 不一致 |
| 宽泛规则判定、上游过滤、清单 | `breadth.py`、`data/` | ✓ | 案例测试；真实数据过滤 0 条、列出 554 条 |
| 来源标注与合并溯源 | `provenance.py`、`annotate.py` | ✓ | 单元与属性测试；真实数据 0 条输入无法溯源 |
| 来源获取、快照、Happy Eyeballs | `sources/` | ✓ | 伪造传输测试；真实网络 |
| 构建、输出、更新说明、发布暂存 | `build.py`、`emit.py`、`report.py`、`publish.py` | ✓ | 端到端测试；两次构建逐字节一致 |
| 验证（语义层、内核层）、explain | `verify/`、`explain.py`、`tools/kernel-adapter/` | ✓ | Mihomo v1.19.33 实测 |
| 工具锁与准备 | `tools.py`、`tools.lock.json` | ✓ | 下载并校验 SHA-256 |
| 每日工作流、CI | `.github/workflows/`、`scripts/` | ✓ | 本地演练 6 个场景；**尚未在 GitHub 上运行** |
| 文档、开源资料、安装包 | `README.md`、`docs/` 等 | ✓ | 链接检查；wheel 在仓库外安装运行 |

## 最近一次验证

2026-11-09 · Windows 10 x64 · Python 3.13.18 · uv 0.13.6

- `pytest` 417 通过（含 kernel 标记）；`ruff check`、`ruff format --check`、`mypy --strict` 通过。
- 真实 profile：`build` 约 24 s，规则文件 7.4 MB（含来源标注）；语义层与内核层 0 不一致（内核层 50,004 个请求），59 个 provider 的加载条目数与文件一致。
- `scripts/rehearse-daily.sh` 6 个场景全部通过，连续 6 次。
- 性能细节见 [performance](../design/performance.md)。

## 已知问题

- subconverter 行为依据 fork 源码模拟，尚未在实际部署上验证；Linux 上的测试与性能待 CI 在 GitHub 上运行后补充。
- 宽泛关键词表需随使用补充；DOMAIN-REGEX 是否匹配一切用 Python `re` 近似判断。
- 演练脚本曾有一次在场景 4 中途退出且无输出，之后未能复现；脚本已改为失败时打印日志末尾。
- `rulesets.toml` 66 条，超过 subconverter 外部配置的 64 条上限；不影响现有接入方式，保留提示。

## 下一步

1. 按[首次启用](../guide/daily-automation.md#首次启用)创建仓库并推送、试运行、打开发布、切换订阅（许可证已定为 GPL-3.0-or-later）。
2. 设计私有输入：让服务器网段等内容参与生成规则，但不出现在公开仓库中。
3. 之后：MRS 输出（与 YAML 同目录同名）、Web、AI 建议。
