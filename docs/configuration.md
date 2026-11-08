# 配置文件

默认位置 `config/domainrouter_v2.toml`，所有命令都可以用 `--config` 指定其他文件。未知字段、非法值都会报错，不会被静默忽略。

```toml
schema_version = 1
project_root = ".."          # 相对于本文件所在目录；其余相对路径都以项目根为基准

[paths]
rules = "my.wei"
groups = "subconverter_config/groups.toml"
state = ".cache/domainrouter_v2"   # 来源快照与工具目录

[output]
directory = "dist"
base_url = "https://raw.githubusercontent.com/<owner>/domainrouter_v2/release"
interval_seconds = 21600           # 写入 rulesets.toml 的更新间隔

[policy]
allow_empty_collections = []       # 允许为空的合集名

[fetch]
max_workers = 8
max_attempts = 3
connect_timeout_seconds = 10
read_timeout_seconds = 30
total_timeout_seconds = 120
max_response_bytes = 33554432
shrink_threshold = 0.5             # 条目数比上次成功少一半以上视为上游异常
max_invalid_ratio = 0.2            # 写法错误的行超过 20% 视为格式异常
stale_warning_days = 7             # 连续失败超过该天数时在更新说明顶部提示
```

## 字段说明

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `project_root` | `".."` | 项目根目录，相对配置文件所在目录 |
| `paths.rules` | `my.wei` | 手写规则文件 |
| `paths.groups` | `subconverter_config/groups.toml` | 策略组定义，校验后原样输出 |
| `paths.state` | `.cache/domainrouter_v2` | 来源快照、健康记录、验证工具 |
| `output.directory` | `dist` | 构建输出目录。不能是项目根、源码目录或任何输入的上级目录 |
| `output.base_url` | 必填 | 规则文件的发布地址前缀，写进 `rulesets.toml`。不能含账号、查询参数或片段 |
| `output.interval_seconds` | `21600` | provider 的更新间隔（秒） |
| `policy.allow_empty_collections` | `[]` | 被引用但可以为空的合集 |
| `fetch.*` | 见上 | 下载并发、重试、超时、大小上限与健康检查阈值 |

`--out` 只改变本次写出的目录，不改变发布地址。

## 目录约定

| 路径 | 内容 | 是否提交 |
| --- | --- | --- |
| `my.wei`、`subconverter_config/groups.toml` | 你的输入 | 是 |
| `config/domainrouter_v2.toml` | 构建配置 | 是 |
| `.cache/domainrouter_v2/sources/` | 每个来源最近一次成功的规范化成员 | 否（CI 中保存在 `state` 分支） |
| `.cache/domainrouter_v2/status.json` | 来源健康记录 | 否（同上） |
| `.cache/domainrouter_v2/tools/` | `tools prepare` 准备的验证工具 | 否 |
| `dist/` | 构建输出 | 否（CI 发布到 `release` 分支） |
