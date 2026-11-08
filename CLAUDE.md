# domainrouter_v2 · Agent 工作约定

把用户的 `my.wei` 与上游规则编译为优化后的 Mihomo rule-provider（YAML）及 subconverter 用的 `rulesets.toml`、`groups.toml`，每天由 GitHub Actions 刷新发布。

## 先读什么

1. [docs/development/progress.md](docs/development/progress.md)：当前进度、最近验证、下一步（唯一状态记录）。
2. [docs/decisions/](docs/decisions/)：已采纳的重要决定；与规范冲突时以决定为准。
3. [docs/rules/merge-cases.md](docs/rules/merge-cases.md)：规则转换与合并的语义契约，每个案例对应测试。
4. [docs/architecture.md](docs/architecture.md)：管线、模块职责与依赖方向、验证层级。
5. [docs/v2-implementation-spec.md](docs/v2-implementation-spec.md)：实施规范 1.5（入口 + 四份分册），只读不改。

进度记录可能过期：恢复工作时以实际代码、`git log`/`git status` 和重新运行的检查为准。

## 硬性边界

- 不创建/推送远端、不实际发布、不改 VPS、不实施 Web/AI。只做本地 git 提交，里程碑结束时提交。
- 不运行 v1 旧脚本；v1 资料只读，来自 `angwz/DomainRouter@5bcb86f`，缓存于 `.cache/migration-v1/`。
- 手写的 `my.wei` 与 `[Rules]` 是用户有意为之：只报告、不改写。上游规则只保留匹配条件。
- 只支持有官方文档的来源格式；不确定的语义查官方文档或 Mihomo 源码（v1.19.33），不猜。
- 正确性优先：去重合并不得扩大或缩小匹配集合；做不到的情况明确报告，不静默丢弃。

## 常用命令

```sh
uv sync --locked                          # 安装锁定依赖（Python 3.13）
uv run --locked ruff check                # 静态检查
uv run --locked ruff format --check       # 格式检查
uv run --locked mypy                      # 类型检查（strict）
uv run --locked pytest -m "not kernel"    # 离线测试
uv run --locked domainrouter_v2 tools prepare && uv run --locked pytest -m kernel
uv run --locked domainrouter_v2 fetch|build|verify --level kernel|explain --host x
scripts/rehearse-daily.sh                 # 每日流程本地演练（6 个场景）
```

Windows 终端输出中文时设置 `PYTHONIOENCODING=utf-8`（CLI 自身已强制 UTF-8）。

## 代码约定

- src 布局：`src/domainrouter_v2/`；依赖方向见 architecture。核心模块不联网，网络只在 `sources/` 与 `tools.py`。
- 代码注释用简体中文，解释原因、不变量和复杂度，不逐行复述。
- 先写简单直接的实现；出现真实重复再抽象。不吞异常、不静默降级。
- 每个可验证小目标：实现 → 相关测试 → 整理（删除废弃分支/临时补丁）→ 同步文档与 progress。
- 文档中的命令、路径、配置键必须与实现一致；同一事实只在一处主说明，其他地方链接。
- 未运行的验证不写成通过；性能数字只写实测值（见 docs/performance.md）。
- Windows 上用 Python 写文件时用 `write_bytes`，避免引入 CRLF；`.gitattributes` 统一为 LF。

## 阶段

M1 解析与模型 → M2 来源、优化与输出 → M3 内核验证与性能 → M4a 迁移、每日工作流与开源交付（均已完成，见 progress）。M4b（远端与生产启用、许可）留给用户另行授权。
