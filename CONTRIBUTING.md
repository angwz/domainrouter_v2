# 参与开发

## 这是一个自用仓库

仓库根目录的 `my.wei`、`subconverter_config/groups.toml` 与 `release` 分支上的规则，是维护者本人每天使用的配置。因此：

- **欢迎提意见。** 发现转换错误、合并问题或想要的功能，请开 [Issue](https://github.com/angwz/domainrouter_v2/issues)，附上规则原文与期望结果。
- **不接受个性化规则。** 添加或修改分流规则的请求不会进入本仓库的发布。
- **想按自己的需要使用，请 fork。** 在自己的副本中修改 `my.wei`、`groups.toml`，把 `config/domainrouter_v2.toml` 的 `output.base_url` 改为自己仓库的地址，再按[首次启用](docs/guide/daily-automation.md#首次启用)打开每日流程。副本中的任何改动都不会影响本仓库。

Pull request 仅对协作者开放；来自外部的工作流运行一律需要维护者批准。下面的内容供维护者与协作者参考。

## 环境

- [uv](https://docs.astral.sh/uv/) 0.13 或更新；Python 3.13 由 uv 自动准备。
- Windows 与 Linux 均可。内核层验证会额外下载 Mihomo、Go 与地理数据（约 300 MB，含 Go 模块）。

```sh
uv sync --locked
```

## 检查命令

```sh
uv run --locked ruff check             # 静态检查
uv run --locked ruff format --check    # 格式
uv run --locked mypy                   # 类型（strict）
uv run --locked pytest -m "not kernel" # 离线测试，不需要任何外部工具
uv run --locked domainrouter_v2 tools prepare
uv run --locked pytest -m kernel       # 真实 Mihomo 对照
scripts/rehearse-daily.sh              # 每日流程本地演练
```

提交前至少运行前四项。改动解析、优化或输出时，再运行内核层测试。

## 加一条回归

规则语义的唯一来源是 [docs/rules/merge-cases.md](docs/rules/merge-cases.md)。修改行为时：

1. 先在 merge-cases 中写清「输入 → 输出 → 原因」以及依据（官方文档或 Mihomo 源码）。
2. 在 `tests/` 的对应文件中加参数化用例：格式适配器放 `tests/parse/test_formats.py`，手写语法放 `tests/parse/test_document.py`，去重合并放 `tests/optimize/`。
3. 涉及包含判定或合并时，确认属性测试（hypothesis）仍然通过。

## 新增来源格式

1. 必须有官方语法文档，并在模块文档字符串中注明链接。没有官方文档的格式不接受。
2. 在 `src/domainrouter_v2/parse/formats/` 新增适配器，返回 `ParseResult`：能转换的进 `entries`，合法但无法转换的进 `skipped` 并写明原因。整份内容不符合格式时抛 `SourceFormatError`。
3. 在 `parse/formats/__init__.py` 登记格式名；只有当内容不会与已有格式混淆时，才加入自动识别。
4. 补充 merge-cases 与测试。

## 新增规则类型

在 `src/domainrouter_v2/registry.py` 登记：分区（domain/ipcidr/classical/逻辑/控制）、成本次序、是否目标 IP 条件、带 `src` 时等价的来源类型。其他客户端的同义名放进 `ALIASES`；Mihomo 没有等价条件的放进 `UNSUPPORTED` 并写明原因。

## 约定

- 代码注释用简体中文，解释原因、不变量和复杂度，不逐行复述代码。
- 不吞异常、不静默降级；无法处理的情况通过诊断明确报告。
- 文档中的命令、路径、配置键必须与实现一致。
- 不需要任何生产凭据、订阅或节点信息；测试只使用 `example.com`、`192.0.2.0/24` 等保留示例地址。
- 提交信息说明改了什么、为什么。
