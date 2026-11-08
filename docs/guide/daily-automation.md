# 每日自动更新

工作流 [`.github/workflows/daily-rules.yml`](../../.github/workflows/daily-rules.yml) 每天刷新全部上游、重新构建、验证，通过后发布到 `release` 分支。

> 代码推送到 GitHub 后，定时构建与验证即开始运行；只有设置了 `PUBLISH_ENABLED` 才会发布。当前状态见[进度](../development/progress.md)。

## 时间

- 定时：`cron: "17 20 * * *"`，即每天 UTC 20:17，香港时间 04:17。
- 手动：在 Actions 页面对 *Daily rules* 点 *Run workflow*，走完全相同的流程。
- GitHub 的定时任务可能延迟，不是准点保证。公开仓库连续 60 天没有活动时，GitHub 会自动停用定时工作流，需要在 Actions 页面重新启用。本项目不会用空提交维持活跃。

## 每次运行做什么

构建作业（只读权限）调用 [`scripts/daily-build.sh`](../../scripts/daily-build.sh)：

1. 从 `state` 分支恢复每个来源上次成功的快照。
2. `fetch`：获取全部上游。单个来源失败（网络错误、非 2xx、HTML 页面、空内容、格式异常、条目数骤降一半以上）时沿用它的旧快照，其余来源照常更新。新来源第一次就失败时，本次运行失败。
3. `check`：检查 `my.wei`、`groups.toml` 与配置。
4. `tools prepare` + `verify --level kernel`：语义层与内核层验证，任一不一致即失败。
5. `publish`：构建并与 `release` 分支的当前内容比较。有变化才写入新文件和更新说明；更新说明同时写进本次运行的 Job Summary。

发布作业仅在仓库变量 `PUBLISH_ENABLED` 为 `true` 时运行，并单独获得写权限。它调用 [`scripts/daily-publish.sh`](../../scripts/daily-publish.sh)，把本次已验证的内容快进推送到 `release` 与 `state` 分支：

- 内容没变的分支不提交。
- 从不强推；如果远端被并发改动，推送失败，本次运行失败。
- 定时与手动运行共用同一把并发锁，不会互相取消。
- 任一步失败时，`release` 保持上一版完整内容，不会出现半套文件。

## 分支

| 分支 | 内容 | 谁写 |
| --- | --- | --- |
| `main` | 代码、`my.wei`、`groups.toml`、配置 | 你 |
| `release` | `clash-domain/`、`clash-ipcidr/`、`clash-classic/`、`rulesets.toml`、`groups.toml`、`manifest.json`、`reports/` | 每日工作流 |
| `state` | `sources/`（各来源规范化快照）、`status.json`（健康记录） | 每日工作流 |

`reports/latest.md` 是最近一次有变化时的更新说明，`reports/changes.json` 是同样内容的机器可读版本。`reports/broad-rules.md` 是当前规则文件中的宽泛规则清单（见 [broad-rules](../rules/broad-rules.md)），内容变化同样会触发发布。

## 首次启用

按顺序进行。前四步只需做一次，之后每天自动运行。

**1. 推送代码**

- 在 GitHub 创建公开仓库 `angwz/domainrouter_v2`（不勾选自动生成 README、LICENSE、.gitignore），推送 `main`。
- 仓库必须公开：subconverter 通过 `raw.githubusercontent.com` 匿名读取规则文件。
- `config/domainrouter_v2.toml` 的 `output.base_url` 应为 `https://raw.githubusercontent.com/angwz/domainrouter_v2/release`；仓库名不同时同步修改。

**2. 检查 Actions 设置**（*Settings → Actions → General*）

- *Actions permissions*：保持默认的 *Allow all actions*；如果改成了限制模式，需放行 `actions/*` 与 `astral-sh/setup-uv`。
- *Workflow permissions*：保持默认的只读即可。工作流在发布作业中显式申请 `contents: write`。

**3. 试运行**

- 推送后 CI 会自动运行；在 Actions 页面确认 *CI* 通过。
- 手动运行一次 *Daily rules*。此时尚未设置发布变量，只构建与验证，结果写在 Job Summary 中。

**4. 打开发布**

- 在 *Settings → Secrets and variables → Actions → Variables* 新增 `PUBLISH_ENABLED`，值为 `true`。
- 再手动运行一次 *Daily rules*，确认出现 `release` 与 `state` 两个分支，并打开 `release/reports/latest.md` 检查。

**5. 切换订阅**

- 把 subconverter 引用的 `rulesets.toml`、`groups.toml` 改为 `release` 分支上的地址，保留 v1 地址作为回滚入口。
- 新版本稳定运行一段时间后，再停用 v1 的工作流，避免两套流程同时更新。

## 回滚

- **暂停发布**：删除 `PUBLISH_ENABLED` 变量，或把值改为其他值。构建与验证照常运行，但不再推送。
- **回到某个旧版本**：`release` 分支每次发布都是一个提交。在本地检出该提交的内容，用 `scripts/push-branch.sh` 作为新提交推送回去（不改写历史）：

  ```sh
  git fetch origin release
  mkdir /tmp/old && git archive <旧提交> | tar -x -C /tmp/old
  scripts/push-branch.sh https://github.com/angwz/domainrouter_v2.git release /tmp/old "rollback: 回到 <旧提交>"
  ```

  回滚后应同时暂停发布，否则下一次每日运行会用最新构建覆盖回滚内容。
- **回到 v1**：把 subconverter 的引用改回 v1 的地址。

## 故障排查

| 现象 | 查看 | 处理 |
| --- | --- | --- |
| 运行失败在 fetch | 日志中带 `✗` 的来源、"没有上次成功的副本" | 新来源地址有误或格式需要显式指定，修改 `my.wei` |
| 某来源长期失败 | 更新说明顶部"可能已失效的来源" | 确认不再需要后从 `my.wei` 删除 |
| 失败在 check | 诊断中的 `error[...]` 与位置 | 按提示修改输入 |
| 失败在 verify | 不一致的请求与规则 | 这是工具缺陷，请附日志反馈 |
| 推送失败 | push 步骤的拒绝信息 | 远端被手动改动；检查后重新运行 |
| 定时没有运行 | Actions 页面是否显示 *disabled* | 重新启用工作流 |

## 本地演练

```sh
scripts/rehearse-daily.sh
```

用本地裸仓库代替 GitHub 远端、本机 HTTP 服务代替上游，调用与工作流相同的两个脚本，并逐项断言以下 6 个场景：首次发布、无变化不提交、上游变化发布新版本、来源 404 沿用旧副本、内容骤降视为异常、新来源首次失败时整次失败且不发布。默认使用语义层验证；设 `VERIFY_LEVEL=kernel` 则同时做内核层验证（需先运行 `tools prepare`）。
