"""release 分支的 README：已发布规则的一览、下载地址与几种取用方式。

每次构建都会重新生成，列表、条目数与地址始终与发布内容一致。
内容只由输入决定（不含时间），两次构建逐字节相同；条目数变化时随规则一起发布。

读者不止一种：整套照搬的 subconverter 用户、只挑几个规则集的 Mihomo 用户、
以及把这里当作上游之一来收集规则的人。文案按这三种用法组织。
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlsplit

from domainrouter_v2.planner import CLASSICAL, DOMAIN, IPCIDR, Artifact, Partition, Plan

# 与 .github/workflows/daily-rules.yml 的 cron 保持一致（UTC 22:00）。
SCHEDULE_TEXT = "每天北京时间 06:00 前后"
PROJECT_URL = "https://github.com/angwz/domainrouter_v2"

_BEHAVIOR = {DOMAIN: "domain", IPCIDR: "ipcidr", CLASSICAL: "classical"}
_BUILTIN = frozenset({"DIRECT", "REJECT"})


def release_readme(
    plan: Plan, base_url: str, resource_url: Callable[[str], str], *, mrs: bool
) -> bytes:
    artifacts = [a for a in plan.artifacts.values() if a.partitions()]
    lines = [
        "# DomainRouter v2 · 规则发布",
        "",
        f"这里是 [DomainRouter v2]({PROJECT_URL}) 每天自动生成的规则。它们首先服务于维护者自己的"
        "分流配置，也欢迎任何人取用：整套照搬、只挑几个规则集，或者像维护者收集上游一样，"
        "把这里当作你的上游之一。",
        "",
        f"- **更新**：{SCHEDULE_TEXT}，内容没有变化时不产生新提交。",
        "- **来源**：规则数据来自各上游规则集，经去重合并后发布，适用上游原有的条款。",
        "- **来历**：YAML 文件开头列出来源，每条规则的同行注释标出它来自哪个上游。",
        "- **说明**：本次变化见 [reports/latest.md](reports/latest.md)，"
        "范围较大的规则见 [reports/broad-rules.md](reports/broad-rules.md)。",
        "",
        *_catalog(artifacts, mrs=mrs),
        "",
        *_formats(mrs=mrs),
        "",
        *_addresses(base_url),
        "",
        "## 取用方式",
        "",
        *_mihomo_usage(artifacts, resource_url, mrs=mrs),
        "",
        *_collector_usage(resource_url, artifacts),
        "",
        *_subconverter_usage(resource_url),
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _catalog(artifacts: list[Artifact], *, mrs: bool) -> list[str]:
    lines = [
        "## 规则一览",
        "",
        "| 规则集 | behavior | 条目 | 维护者的用法 | 下载 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for artifact in artifacts:
        name = " + ".join(artifact.collections)
        targets = "、".join(artifact.targets)
        for partition in artifact.partitions():
            path = artifact.path(partition)
            links = f"[YAML]({path})"
            if mrs and partition is not CLASSICAL:
                links += f" · [MRS]({_mrs(path)})"
            count = len(artifact.members(partition))
            lines.append(f"| {name} | `{_BEHAVIOR[partition]}` | {count:,} | {targets} | {links} |")
    lines += [
        "",
        "「维护者的用法」只是参考：维护者有多个地区的节点，会把面向不同地区的规则集分别指向"
        "对应的地区组。你的节点布局不同，按自己的情况安排即可。",
    ]
    return lines


def _formats(*, mrs: bool) -> list[str]:
    lines = ["## 格式", ""]
    if mrs:
        lines += [
            "- **MRS**：Mihomo 的二进制规则集，体积小、加载快，适合直接交给 Mihomo；"
            "不能阅读。只有 `domain` 与 `ipcidr` 有 MRS。",
            "- **YAML**：标准的 rule-provider（`payload:`），带来源注释，适合阅读、审查，"
            "或作为你自己构建流程的上游；Mihomo 同样可以直接加载。",
        ]
    else:
        lines.append(
            "- **YAML**：标准的 rule-provider（`payload:`），带来源注释，Mihomo 可以直接加载，"
            "也适合作为你自己构建流程的上游。"
        )
    lines.append(
        "- `behavior` 由目录决定：`clash-domain` → `domain`，`clash-ipcidr` → `ipcidr`，"
        "`clash-classic` → `classical`。"
    )
    return lines


def _addresses(base_url: str) -> list[str]:
    raw_example = base_url.rstrip("/") + "/<文件>"
    lines = [
        "## 下载地址",
        "",
        "把 `<文件>` 换成上表中的路径：",
        "",
        f"- GitHub：`{raw_example}`",
    ]
    mirror = _jsdelivr(raw_example)
    if mirror:
        lines.append(f"- jsDelivr：`{mirror}`（国内访问较快；CDN 缓存，内容最多可能晚约 12 小时）")
    return lines


def _mihomo_usage(
    artifacts: list[Artifact], resource_url: Callable[[str], str], *, mrs: bool
) -> list[str]:
    """用第一个同时有 domain 与 ipcidr 文件的规则集举例；没有时退回第一个规则集。"""
    lines = [
        "### 挑几个规则集，用在 Mihomo 中",
        "",
        "每个文件就是一个 rule-provider。",
    ]
    sample = next(
        (a for a in artifacts if DOMAIN in a.partitions() and IPCIDR in a.partitions()),
        artifacts[0] if artifacts else None,
    )
    if sample is None:
        return lines
    # 维护者的目标是内置策略时照用（读起来自然）；自定义组名对访客无意义，改用占位的 PROXY。
    target = next((t for t in sample.targets if t in _BUILTIN), "PROXY")
    providers: list[str] = []
    rules: list[str] = []
    for partition in sample.partitions():
        providers += _provider(sample, partition, resource_url, mrs=mrs)
        # ipcidr 加 no-resolve：未解析的域名请求不会为了匹配网段而触发 DNS。
        suffix = ",no-resolve" if partition is IPCIDR else ""
        rules.append(f"  - RULE-SET,{_stem(sample.path(partition))},{target}{suffix}")
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
        "策略组按自己的节点填写，规则的先后就是匹配优先级。只有一两个地区的节点时，"
        "面向其他地区的规则集可以指向同一个代理组，或者干脆不引用。",
    ]


def _provider(
    artifact: Artifact, partition: Partition, resource_url: Callable[[str], str], *, mrs: bool
) -> list[str]:
    path = artifact.path(partition)
    binary = mrs and partition is not CLASSICAL
    published = _mrs(path) if binary else path
    return [
        f"  {_stem(path)}:",
        "    type: http",
        f"    behavior: {_BEHAVIOR[partition]}",
        f"    format: {'mrs' if binary else 'yaml'}",
        f"    url: {resource_url(published)}",
        f"    path: ./rule-providers/{published.rsplit('/', 1)[1]}",
        "    interval: 86400",
    ]


def _collector_usage(resource_url: Callable[[str], str], artifacts: list[Artifact]) -> list[str]:
    sample = next((a for a in artifacts if DOMAIN in a.partitions()), None)
    lines = [
        "### 作为你的上游",
        "",
        "把 YAML 地址交给你自己的规则工具即可。转换时请按 Mihomo 的语义理解域名写法："
        "`+.example.com` 是自身及全部子域，`.example.com` 只匹配子域，`example.com` 只匹配自身。",
    ]
    if sample is not None:
        url = resource_url(sample.path(DOMAIN))
        lines += [
            "",
            "如果你也使用 DomainRouter v2，在 `my.wei` 中写明格式即可：",
            "",
            "```text",
            f"@source {url} format=domain",
            "```",
        ]
    return lines


def _subconverter_usage(resource_url: Callable[[str], str]) -> list[str]:
    return [
        "### 整套照搬（subconverter）",
        "",
        "[rulesets.toml](rulesets.toml) 与 [groups.toml](groups.toml) 是维护者自用的完整配置：",
        "",
        f"- `{resource_url('rulesets.toml')}`",
        f"- `{resource_url('groups.toml')}`",
        "",
        "`rulesets.toml` 中每个规则集都指向 `groups.toml` 里的某个策略组，而这些组是按维护者"
        "多个地区的节点编排的。节点布局不同时，建议复制一份 `groups.toml` 按自己的节点调整，"
        "保留 `rulesets.toml` 引用到的组名；需要改动规则本身时，fork "
        f"[本项目]({PROJECT_URL}) 生成你自己的发布。",
    ]


def _mrs(yaml_path: str) -> str:
    return yaml_path.removesuffix(".yaml") + ".mrs"


def _stem(path: str) -> str:
    return path.rsplit("/", 1)[1].rsplit(".", 1)[0]


def _jsdelivr(raw_url: str) -> str:
    """raw.githubusercontent.com/<owner>/<repo>/<ref>/<path> 转为 jsDelivr 地址；其他主机不推断。"""
    parts = urlsplit(raw_url)
    segments = parts.path.lstrip("/").split("/", 3)
    if parts.netloc != "raw.githubusercontent.com" or len(segments) < 4:
        return ""
    owner, repo, ref, path = segments
    return f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}"
