"""release 分支的 README：可取用的规则一览与用法，供访客直接取用。

每次构建都会重新生成，所以列表、条目数与地址始终与发布内容一致。
内容只由输入决定（不含时间），两次构建逐字节相同；条目数变化时随规则一起发布。
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlsplit

from domainrouter_v2.planner import CLASSICAL, DOMAIN, IPCIDR, Artifact, Plan

# 与 .github/workflows/daily-rules.yml 的 cron 保持一致（UTC 22:00）。
SCHEDULE_TEXT = "每天北京时间 06:00 前后"
PROJECT_URL = "https://github.com/angwz/domainrouter_v2"

_BEHAVIOR = {DOMAIN: "domain", IPCIDR: "ipcidr", CLASSICAL: "classical"}
_BUILTIN = frozenset({"DIRECT", "REJECT"})


def release_readme(plan: Plan, base_url: str, resource_url: Callable[[str], str]) -> bytes:
    artifacts = [a for a in plan.artifacts.values() if a.partitions()]
    raw_example = base_url.rstrip("/") + "/<文件>"
    lines = [
        "# DomainRouter v2 · 规则发布",
        "",
        f"这里是 [DomainRouter v2]({PROJECT_URL}) 每天自动生成的规则，欢迎自由取用。",
        "规则按维护者的分流偏好整理，可能随时调整；规则数据来自各上游规则集，适用其原有条款。",
        "",
        f"- **更新**：{SCHEDULE_TEXT}，内容没有变化时不产生新提交。",
        "- **说明**：本次更新说明见 [reports/latest.md](reports/latest.md)，"
        "范围较大的规则见 [reports/broad-rules.md](reports/broad-rules.md)。",
        "- **来历**：每个文件开头列出来源，每条规则的同行注释标出它来自哪个上游。",
        "",
        "## 规则一览",
        "",
        "| 规则集 | behavior | 条目 | 维护者的用法 | 文件 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for artifact in artifacts:
        name = " + ".join(artifact.collections)
        targets = "、".join(artifact.targets)
        for partition in artifact.partitions():
            path = artifact.path(partition)
            count = len(artifact.members(partition))
            lines.append(
                f"| {name} | `{_BEHAVIOR[partition]}` | {count:,} | {targets} | [{path}]({path}) |"
            )
    lines += [
        "",
        "## 下载地址",
        "",
        "把下面地址中的 `<文件>` 换成上表中的路径：",
        "",
        f"- GitHub：`{raw_example}`",
    ]
    mirror = _jsdelivr(raw_example)
    if mirror:
        lines.append(f"- jsDelivr 加速：`{mirror}`（CDN 缓存，内容最多可能晚约 12 小时）")
    lines += ["", *_mihomo_usage(artifacts, resource_url), "", *_subconverter_usage(resource_url)]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _mihomo_usage(artifacts: list[Artifact], resource_url: Callable[[str], str]) -> list[str]:
    """用第一个同时有 domain 与 ipcidr 文件的规则集举例；没有时退回第一个文件。"""
    sample = next(
        (a for a in artifacts if DOMAIN in a.partitions() and IPCIDR in a.partitions()),
        artifacts[0] if artifacts else None,
    )
    lines = [
        "## 在 Mihomo 中使用",
        "",
        "每个文件是一个 rule-provider。`behavior` 按目录选择：`clash-domain` → `domain`，"
        "`clash-ipcidr` → `ipcidr`，`clash-classic` → `classical`；文件都是 YAML 格式。",
    ]
    if sample is None:
        return lines
    # 维护者的目标是内置策略时照用（读起来自然）；自定义组名对访客无意义，改用占位的 PROXY。
    target = next((t for t in sample.targets if t in _BUILTIN), "PROXY")
    providers: list[str] = []
    rules: list[str] = []
    for partition in sample.partitions():
        stem = sample.path(partition).rsplit("/", 1)[1].removesuffix(".yaml")
        providers += [
            f"  {stem}:",
            "    type: http",
            f"    behavior: {_BEHAVIOR[partition]}",
            "    format: yaml",
            f"    url: {resource_url(sample.path(partition))}",
            f"    path: ./rule-providers/{stem}.yaml",
            "    interval: 86400",
        ]
        # ipcidr 加 no-resolve：未解析的域名请求不会为了匹配网段而触发 DNS。
        suffix = ",no-resolve" if partition is IPCIDR else ""
        rules.append(f"  - RULE-SET,{stem},{target}{suffix}")
    return [
        *lines,
        "",
        "```yaml",
        "rule-providers:",
        *providers,
        "",
        "rules:",
        *rules,
        "```",
        "",
        "策略组按自己的配置填写；规则之间的先后就是匹配优先级。",
    ]


def _subconverter_usage(resource_url: Callable[[str], str]) -> list[str]:
    return [
        "## 在 subconverter 中使用",
        "",
        "[rulesets.toml](rulesets.toml) 与 [groups.toml](groups.toml) 是维护者自用的完整配置，"
        "可以直接引用：",
        "",
        f"- `{resource_url('rulesets.toml')}`",
        f"- `{resource_url('groups.toml')}`",
        "",
        "其中的策略组名称是维护者的命名；只想用部分规则时，从上表挑选文件写进自己的配置更合适。",
    ]


def _jsdelivr(raw_url: str) -> str:
    """raw.githubusercontent.com/<owner>/<repo>/<ref>/<path> 转为 jsDelivr 地址；其他主机不推断。"""
    parts = urlsplit(raw_url)
    segments = parts.path.lstrip("/").split("/", 3)
    if parts.netloc != "raw.githubusercontent.com" or len(segments) < 4:
        return ""
    owner, repo, ref, path = segments
    return f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}"
