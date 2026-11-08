"""受限 YAML 读取：只接受规则来源需要的简单结构。

拒绝锚点、别名、merge key、自定义 tag、重复键与多文档（规范 §5）：
仅靠 safe_load 不能限制资源与歧义。
上游的 ``payload:`` 文件通常有十万行级别，因此先尝试逐行快速路径：
只在每一行都是「``payload:``/``rules:`` 键、``- 标量`` 项、注释或空行」时使用；
否则回退到完整解析器（含上述检查）。两条路径对同一输入必须给出相同结果，由测试保证。
"""

from __future__ import annotations

import re
from typing import Any

import yaml

_KEY_LINE = re.compile(r"^(payload|rules)\s*:\s*(#.*)?$")
_ITEM_LINE = re.compile(r"^\s+-\s+(.*)$")
_PLAIN_SAFE = re.compile(r"^[^\s'\"#&*!|>%@`{}\[\],:?-][^#]*?$|^-[^\s].*$")


class YamlStructureError(ValueError):
    pass


def load_list_document(text: str, keys: frozenset[str] | None = None) -> dict[str, list[str]]:
    """读取形如 ``payload: [字符串…]`` 的 YAML，返回 {键: 字符串列表}。

    值必须是字符串序列；布尔、数字、null 等非字符串条目报错，不转换成貌似有效的规则。
    ``keys`` 不为 None 时只检查并返回这些键（用于完整 Clash 配置，其余键可以是任意结构）。
    """
    fast = _fast_path(text)
    if fast is not None:
        return fast if keys is None else {k: v for k, v in fast.items() if k in keys}
    return _full_parse(text, keys)


def _fast_path(text: str) -> dict[str, list[str]] | None:
    result: dict[str, list[str]] = {}
    current: list[str] | None = None
    for raw in text.removeprefix("﻿").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        key = _KEY_LINE.match(line)
        if key:
            if key.group(1) in result:
                return None  # 重复键交给完整解析器报错
            current = result.setdefault(key.group(1), [])
            continue
        item = _ITEM_LINE.match(line)
        if item is None or current is None:
            return None
        value = _scalar(item.group(1))
        if value is None:
            return None
        current.append(value)
    return result or None


def _scalar(token: str) -> str | None:
    """解析单行标量；任何不确定的写法返回 None（回退完整解析）。"""
    body = token.strip()
    if body.startswith("'"):
        end = body.rfind("'")
        rest = body[end + 1 :].strip()
        if end == 0 or (rest and not rest.startswith("#")):
            return None
        inner = body[1:end]
        if "'" in inner.replace("''", ""):
            return None
        return inner.replace("''", "'")
    if body.startswith('"'):
        end = body.rfind('"')
        rest = body[end + 1 :].strip()
        inner = body[1:end]
        if end == 0 or "\\" in inner or '"' in inner or (rest and not rest.startswith("#")):
            return None
        return inner
    # 未加引号：去掉以空白开头的行尾注释，并排除会被 YAML 解释为非字符串的值
    value = re.split(r"\s+#", body, maxsplit=1)[0].strip()
    if not value or not _PLAIN_SAFE.match(value) or ": " in value or value.endswith(":"):
        return None
    if _is_non_string_plain(value):
        return None
    return value


_RESOLVER = yaml.resolver.Resolver()
_STR_TAG = "tag:yaml.org,2002:str"


def _is_non_string_plain(value: str) -> bool:
    """用 YAML 1.1 隐式解析规则判断未加引号的值是否会变成布尔、数字、null 等。"""
    tag: str = _RESOLVER.resolve(yaml.ScalarNode, value, (True, False))  # type: ignore[no-untyped-call]
    return tag != _STR_TAG


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False) -> Any:
    seen: set[Any] = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise YamlStructureError("不支持 YAML merge key（<<）")
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise YamlStructureError(f"重复的键：{key!r}（第 {key_node.start_mark.line + 1} 行）")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _check_events(text: str) -> None:
    documents = 0
    for event in yaml.parse(text, Loader=yaml.SafeLoader):
        if isinstance(event, yaml.DocumentStartEvent):
            documents += 1
            if documents > 1:
                raise YamlStructureError("不支持多文档 YAML")
        elif isinstance(event, yaml.AliasEvent):
            raise YamlStructureError("不支持 YAML 别名（*）")
        elif isinstance(event, yaml.NodeEvent) and event.anchor is not None:
            raise YamlStructureError("不支持 YAML 锚点（&）")
        if isinstance(event, yaml.ScalarEvent | yaml.CollectionStartEvent):
            tag = event.tag
            if tag is not None and not getattr(event, "implicit", (True,))[0] and tag != "!":
                raise YamlStructureError(f"不支持自定义 tag：{tag}")


def _full_parse(text: str, keys: frozenset[str] | None = None) -> dict[str, list[str]]:
    try:
        _check_events(text)
        data = yaml.load(text, Loader=_StrictLoader)
    except yaml.YAMLError as exc:
        raise YamlStructureError(f"YAML 语法错误：{exc}") from exc
    if not isinstance(data, dict):
        raise YamlStructureError("顶层必须是映射")
    result: dict[str, list[str]] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise YamlStructureError(f"键必须是字符串：{key!r}")
        if keys is not None and key not in keys:
            continue
        if value is None:
            result[key] = []
            continue
        if not isinstance(value, list):
            result[key] = []  # 非列表键由调用方按需要判断，例如完整配置中的其他字段
            continue
        items: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise YamlStructureError(f"{key} 的条目必须是字符串，实际为 {item!r}")
            items.append(item)
        result[key] = items
    return result
