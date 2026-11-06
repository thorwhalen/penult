"""Render the essay for the places it is reviewed: a GitHub issue comment.

The essay is written once, as ``essay.md`` with front matter (``title``,
``subtitle``) and relative image paths, which is what the ``article`` package
publishes from. GitHub comments cannot see the repository's files, so for the
comment every relative image becomes its ``raw.githubusercontent.com`` URL in an
``<img>`` tag (GitHub keeps ``width``, so an ``inset`` image is drawn narrower, see
:mod:`penult.figures`) and a caption becomes a small centred line under it, the way
the platforms draw captions; the title and subtitle, which Substack shows in their
own fields, are written as a heading.

>>> text = '---\\ntitle: T\\nsubtitle: S\\nimages:\\n  img/a.png: inset\\n---\\n# T\\n\\nA line.\\n\\n![alt](img/a.png "A caption")\\n'
>>> print(render_comment(text, raw_base="https://raw.githubusercontent.com/o/r/main/docs/t/", footer=""))
# T
<BLANKLINE>
*S*
<BLANKLINE>
A line.
<BLANKLINE>
<p align="center"><img src="https://raw.githubusercontent.com/o/r/main/docs/t/img/a.png" alt="alt" width="400"></p>
<BLANKLINE>
<p align="center"><sub>A caption</sub></p>
"""

from __future__ import annotations

import hashlib
import html
import re
from urllib.parse import quote, unquote

from penult.base import PenultError

__all__ = ["essay_fields", "local_images", "render_comment", "text_hash"]

_IMAGE = re.compile(r'!\[([^\]]*)\]\(\s*(?P<src>[^)\s]+)(?:\s+"(?P<cap>[^"]*)")?\s*\)')


def text_hash(text: str) -> str:
    """A short, stable fingerprint of a text, to tell whether it changed.

    >>> text_hash("a") == text_hash("a"), text_hash("a") != text_hash("b")
    (True, True)
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _is_remote(src: str) -> bool:
    return bool(re.match(r"^(https?:|data:|//)", src))


def local_images(markdown: str) -> list[str]:
    """The relative image paths an essay references, in order, without duplicates.

    >>> local_images('![a](img/a.png) ![b](https://x/y.png) ![c](./img/a.png)')
    ['img/a.png']
    """
    seen: list[str] = []
    for found in _IMAGE.finditer(markdown):
        src = _relative(found.group("src"))
        if not _is_remote(src) and src not in seen:
            seen.append(src)
    return seen


def _relative(src: str) -> str:
    src = unquote(src)
    return src[2:] if src.startswith("./") else src


def essay_fields(markdown: str) -> dict:
    """Title, subtitle, tags, slug and body from an essay's Markdown, as ``article`` reads it."""
    from article.base import ArticleError
    from article.md_source import markdown_to_fields

    try:
        return markdown_to_fields(markdown, origin="essay.md")
    except ArticleError as error:
        raise PenultError(f"essay.md: {error}") from error


def render_comment(
    markdown: str, *, raw_base: str, footer: str = "", inset_width: int | None = None
) -> str:
    """The essay as a GitHub comment: heading, subtitle, body with absolute, sized images.

    Image sizes come from the essay's ``images:`` front matter (:mod:`penult.figures`);
    ``inset_width`` overrides the width an ``inset`` is drawn at.
    """
    from penult import figures as layout  # lazily: figures imports this module

    fields = essay_fields(markdown)
    sizes = layout.sizes_from_fields(fields)
    width_kw = {} if inset_width is None else {"inset_width": inset_width}
    body = fields["content_markdown"]

    def absolute(found: re.Match) -> str:
        alt, src, cap = found.group(1), found.group("src"), found.group("cap")
        key = _relative(src)
        if not _is_remote(src):
            src = raw_base + quote(key, safe="/")
        attrs = {
            "src": src,
            "alt": alt,
            **layout.github_attrs(sizes.get(key), **width_kw),
        }
        tag = (
            "<img "
            + " ".join(
                f'{k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items()
            )
            + ">"
        )
        image = f'<p align="center">{tag}</p>'
        return image + (
            f'\n\n<p align="center"><sub>{html.escape(cap)}</sub></p>' if cap else ""
        )

    body = _IMAGE.sub(absolute, body)
    head = [f"# {fields['title']}", ""]
    if fields.get("subtitle"):
        head += [f"*{fields['subtitle']}*", ""]
    out = "\n".join(head) + "\n" + body.strip() + "\n"
    if footer:
        out += "\n---\n\n" + footer.strip() + "\n"
    return out.rstrip("\n")
