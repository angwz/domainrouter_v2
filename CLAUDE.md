# domainrouter_v2 · 代理工作约定

把维护者的 `my.wei` 与上游规则编译为优化后的 Mihomo rule-provider（YAML），以及 subconverter 用的 `rulesets.toml`、`groups.toml`；GitHub Actions 每天刷新并发布。

## 先读什么

1. [docs/development/progress.md](docs/development/progress.md) — 当前进度、最近一次验证、下一步。唯一的状态记录。
2. [docs/development/feedback.md](docs/development/feedback.md) — 维护者提过的全部意见。**每收到一条新意见就追加一行**，处理后更新状态；只写中性总结，不引用原话。
3. [docs/decisions/](docs/decisions/) — 已采纳的决定，与其他文档冲突时以决定为准。
4. [docs/rules/merge-cases.md](docs/rules/merge-cases.md) — 规则转换与合并的语义契约，每个案例都有测试。
5. [docs/design/architecture.md](docs/design/architecture.md) — 管线、模块职责与依赖方向、验证层级。

其余文档从 [docs/README.md](docs/README.md) 进入。[docs/history/spec-1.5/](docs/history/spec-1.5/) 是项目起点的实施规范，已归档，只读。

进度记录可能过期：恢复工作时以实际代码、`git log`、`git status` 与重新运行的检查为准。

## 硬性边界

- 远端操作（推送、发布、改动仓库设置）与 VPS 变更只在维护者明确要求时进行；Web 与 AI 功能尚未立项。
- v1 资料只读，来自 `angwz/DomainRouter@5bcb86f`；不运行 v1 脚本。
- `my.wei` 与 `[Rules]` 中手写的内容是有意为之：只报告，不改写。上游规则只保留匹配条件，过宽的上游规则被过滤并列入清单（[broad-rules](docs/rules/broad-rules.md)）。
- 只支持有官方文档的来源格式；不确定的语义查官方文档或 Mihomo 源码（v1.19.33），不猜。
- 正确性优先：去重合并不得扩大或缩小匹配集合；做不到的情况明确报告，不静默丢弃。

## 呈现

- 维护者对生成文件与文档的审美要求很高。改动输出格式（排序、文件头、注释）时，先给出真实数据的样例。
- 文档同时面向人与代理：结构清晰、措辞克制、信息密度高；可以自由重组段落、文件与目录，改动后保证链接有效。

## 常用命令

```sh
uv sync --locked                          # 安装锁定依赖（Python 3.13）
uv run --locked ruff check                # 静态检查
uv run --locked ruff format --check       # 格式检查
uv run --locked mypy                      # 类型检查（strict）
uv run --locked pytest -m "not kernel"    # 离线测试
uv run --locked domainrouter_v2 tools prepare && uv run --locked pytest -m kernel
uv run --locked domainrouter_v2 fetch|build|verify --level kernel
uv run --locked domainrouter_v2 explain --host x|--ip x|--rule '+.x'
scripts/rehearse-daily.sh                 # 每日流程本地演练（6 个场景）
```

Windows 终端输出中文时设置 `PYTHONIOENCODING=utf-8`（CLI 自身已强制 UTF-8）。

## 代码约定

- src 布局：`src/domainrouter_v2/`；依赖方向见 architecture。核心模块不联网，网络只在 `sources/` 与 `tools.py`。
- 代码注释用简体中文，解释原因、不变量和复杂度，不逐行复述。
- 先写简单直接的实现，出现真实重复再抽象。不吞异常、不静默降级。
- 每个可验证的小目标：实现 → 测试 → 整理（删除废弃分支与临时补丁）→ 同步文档与 progress。
- 文档中的命令、路径、配置键必须与实现一致；同一事实只在一处详述，其他地方链接。
- 未运行的验证不写成通过；性能数字只写实测值（[performance](docs/design/performance.md)）。
- Windows 上用 Python 写文件时用 `write_bytes`，避免 CRLF；`.gitattributes` 统一为 LF。
