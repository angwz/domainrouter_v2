# 实施进度

> 唯一状态记录。区分「已实现」与「已验证」；过期内容直接覆盖。

## 当前

- 里程碑：**M2 收尾 → M3**
- 正在做：语义层验证（未优化 vs 优化的参考解释器对照）、explain 命令；随后准备 Mihomo 内核层验证。

## 已完成

| 内容 | 位置 | 已实现 | 已验证 |
| --- | --- | --- | --- |
| 决策与语义契约 | [decisions/0001](../decisions/0001-deviations-from-spec-1.5.md)、[rules/merge-cases.md](../rules/merge-cases.md) | ✓ | 案例均有对应单元测试 |
| 域名模式与包含判定 | `model/domain.py` | ✓ | 穷举交叉校验 + 1000 例属性测试 |
| 网段精确合并 | `model/ip.py` | ✓ | 1000 例属性测试，与标准库交叉校验 |
| 规则行转换、类型注册表 | `parse/rule_text.py`、`registry.py` | ✓ | 单元测试 |
| 来源格式适配器与自动识别 | `parse/formats/` | ✓ | 单元测试；真实 210 个来源 0 失败、0 跳过 |
| my.wei 解析 | `parse/document.py`、`parse/freeline.py` | ✓ | 单元测试；v1 真实 my.wei 0 错误 |
| domain/classical 优化 | `optimize/` | ✓ | 属性测试：语言不变、无残留包含、幂等 |
| 输出规划（相邻合并、命名碰撞） | `planner.py` | ✓ | 单元测试 |
| 来源获取、快照、健康检查、Happy Eyeballs | `sources/` | ✓ | 伪造传输测试；真实网络运行 |
| 构建、输出、更新说明、发布暂存 | `build.py`、`emit.py`、`report.py`、`publish.py` | ✓ | 端到端测试；真实 profile 构建 |
| CLI：check / fetch / build / publish | `cli.py` | ✓ | 退出码测试 |

## 最近验证（2026-11-08 · Windows 10 x64 · Python 3.13.18）

- `uv run pytest`：327 passed；`ruff check`、`ruff format --check`、`mypy --strict`：通过。
- 真实 profile（v1 固定提交的 my.wei/groups.toml）：
  - `fetch` 冷启动 29 s（210 来源，0 失败）；有快照时 6 s（全部 HTTP 304）。修复前因 IPv6 不通需 17 min，见 `sources/net.py`。
  - `build` 18.5 s，59 个规则文件、`rulesets.toml` 66 条；两次构建逐字节一致。
  - `publish` 第二次运行判定内容未变，release 目录无改动。

## 已知问题与待核验

- `rulesets.toml` 66 条，超过 subconverter 外部配置的 64 条上限（只告警；pref 导入方式不受限，待用户确认其加载方式）。
- 内核层未验证：Mihomo 对 `DST-PORT,a/b-c` 多段写法、逻辑规则子条件中的 `no-resolve`、YAML provider 行解析需 M3 实测。
- `GEOIP,CLOUDFLARE` 等依赖客户端 geo 数据，本项目不校验其存在性。
- 许可证未选定。

## 下一步

1. 语义层验证命令（参考解释器对照未优化/优化产物）与 `explain`。
2. M3：准备 Mihomo v1.19.33 与 Go，编写内核适配器，对真实产物做行为对照与性能基线。
3. M4a：每日工作流、CI、文档、迁移报告、安装包。
