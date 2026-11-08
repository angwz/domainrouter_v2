# 参与开发

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
