# 进度

> 项目的唯一状态记录。区分「已实现」与「已验证」，过期内容直接覆盖，不保留流水账。

## 现在

- **阶段**：v2.0.0 已发布（2026-11-09）。仓库 [angwz/domainrouter_v2](https://github.com/angwz/domainrouter_v2) 公开；每日流程已启用，`release` 与 `state` 分支由工作流维护。
- **待维护者完成**：subconverter 切换到新地址；切换后归档 v1 仓库。

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
| 每日工作流、CI | `.github/workflows/`、`scripts/` | ✓ | 本地演练 6 个场景；GitHub 上试运行与首次发布成功 |
| 文档、开源资料、安装包 | `README.md`、`docs/` 等 | ✓ | 链接检查；wheel 在仓库外安装运行 |

## 最近一次验证

2026-11-09

- 本地（Windows 10 x64 · Python 3.13.18）：`pytest` 417 通过（含 kernel 标记）；`ruff`、`mypy --strict` 通过；`scripts/rehearse-daily.sh` 6 个场景通过。
- GitHub CI：ubuntu-24.04 与 windows-2025 × Python 3.13/3.14 测试、内核层测试、安装包检查全部通过。
- GitHub 每日流程：210 个来源 0 失败；内核层 50,004 个请求 0 不一致，59 个 provider 条目数一致；首次发布写入 `release` 与 `state`。
- 真实 profile 的构建耗时与体积见 [performance](../design/performance.md)。

## 已知问题

- subconverter 行为依据 fork 源码模拟，尚未在实际部署上验证。
- 宽泛关键词表需随使用补充；DOMAIN-REGEX 是否匹配一切用 Python `re` 近似判断。
- 演练脚本曾有一次在场景 4 中途退出且无输出，之后未能复现；脚本已改为失败时打印日志末尾。
- `rulesets.toml` 66 条，超过 subconverter 外部配置的 64 条上限；不影响现有接入方式，保留提示。

## 下一步

1. 维护者切换订阅后：v1 仓库停用工作流、首页注明已迁移、归档。
2. 设计私有输入：让服务器网段等内容参与生成规则，但不出现在公开仓库中。
3. 之后：MRS 输出（与 YAML 同目录同名）、Web、AI 建议。
