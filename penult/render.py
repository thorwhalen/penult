"""Render the essay for the places it is reviewed: a GitHub issue comment.

The essay is written once, as ``essay.md`` with front matter (``title``,
``subtitle``) and relative image paths, which is what the ``article`` package
publishes from. GitHub comments cannot see the repository's files, so for the
comment every relative image becomes its ``raw.githubusercontent.com`` URL and a
caption becomes an italic line under the image; the title and subtitle, which
Substack shows in their own fields, are written as a heading.

>>> text = '---\\ntitle: T\\nsubtitle: S\\n---\\n# T\\n\\nA line.\\n\\n![alt](img/a.png "A caption")\\n'
>>> print(render_comment(text, raw_base="https://raw.githubusercontent.com/o/r/main/docs/t/", footer=""))
# T
<BLANKLINE>
*S*
<BLANKLINE>
A line.
<BLANKLINE>
![alt](https://raw.githubusercontent.com/o/r/main/docs/t/img/a.png)
<BLANKLINE>
*A caption*
"""

from __future__ import annotations

import re
from urllib.parse import quote

__all__ = ["local_images", "render_comment"]

_IMAGE = re.compile(r'!\[([^\]]*)\]\(\s*(?P<src>[^)\s]+)(?:\s+"(?P<cap>[^"]*)")?\s*\)')


def _is_remote(src: str) -> bool:
    return bool(re.match(r"^(https?:|data:|//)", src))


def local_images(markdown: str) -> list[str]:
    """The relative image paths an essay references, in order, without duplicates.

    >>> local_images('![a](img/a.png) ![b](https://x/y.png) ![c](img/a.png)')
    ['img/a.png']
    """
    seen: list[str] = []
    for found in _IMAGE.finditer(markdown):
        src = found.group("src")
        if not _is_remote(src) and src not in seen:
            seen.append(src)
    return seen


def _fields(markdown: str) -> dict:
    from article.md_source import markdown_to_fields

    return markdown_to_fields(markdown, origin="essay.md")


def render_comment(markdown: str, *, raw_base: str, footer: str = "") -> str:
    """The essay as a GitHub comment: heading, subtitle, body with absolute images."""
    fields = _fields(markdown)
    body = fields["content_markdown"]

    def absolute(found: re.Match) -> str:
        alt, src, cap = found.group(1), found.group("src"), found.group("cap")
        if not _is_remote(src):
            src = raw_base + quote(src.lstrip("./"), safe="/")
        image = f"![{alt}]({src})"
        return image + (f"\n\n*{cap}*" if cap else "")

    body = _IMAGE.sub(absolute, body)
    head = [f"# {fields['title']}", ""]
    if fields.get("subtitle"):
        head += [f"*{fields['subtitle']}*", ""]
    out = "\n".join(head) + body.strip() + "\n"
    if footer:
        out += "\n---\n\n" + footer.strip() + "\n"
    return out.rstrip("\n")
