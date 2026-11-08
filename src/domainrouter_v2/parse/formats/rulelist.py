"""规则列表：Surge RULE-SET 文件、Loon 规则文件、Mihomo classical text。

三者的行形态都是 ``TYPE,值[,策略][,参数…]``，类型名经注册表映射到 Mihomo 规范名。
依据：
- Surge https://manual.nssurge.com/rules/ruleset.html （注释 ``#`` ``//`` ``;``；允许行尾注释）
- Loon https://nsloon.app/docs/Rule/
- Mihomo https://wiki.metacubex.one/en/config/rules/
"""

from __future__ import annotations

import re

from domainrouter_v2.parse.formats.base import ParseResult, iter_lines
from domainrouter_v2.parse.formats.common import add_rule
from domainrouter_v2.parse.rule_text import looks_like_rule

_COMMENT_PREFIXES = ("#", "//", ";")
# 行尾注释：只在空白之后出现时识别，避免截断正则中的 # 或 //
_TRAILING_COMMENT = re.compile(r"\s+(//|#|;).*$")
_REGEX_TYPES = ("DOMAIN-REGEX", "URL-REGEX", "PROCESS-NAME-REGEX", "PROCESS-PATH-REGEX")


def parse_rulelist(text: str, dialect: str = "surge") -> ParseResult:
    result = ParseResult(dialect)
    for number, line in iter_lines(text):
        if not line or line.startswith(_COMMENT_PREFIXES) or line == "---":
            continue
        body = line
        if body.startswith("- "):
            body = _unquote(body[2:].strip())
        if not body.upper().startswith(_REGEX_TYPES):
            body = _TRAILING_COMMENT.sub("", body)
        if not looks_like_rule(body):
            result.skip(number, line, "不是规则行", invalid=True)
            continue
        add_rule(result, number, body)
    return result


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text
