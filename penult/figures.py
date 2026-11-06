"""Illustration layout: how big each image is drawn, and where, on every renderer.

The rules come from ``misc/docs/research/2026-11-06-illustration-layout-for-essays.md``
(sourced where it could be, judgment where it says so). The short version:

- An image has a **size class**: ``inset`` (about half the column, centred), ``normal``
  (the column, the default), ``large`` (wider than the column; Substack renders it on
  the web only) or ``full`` (edge to edge; opt-in, for an image that *is* the content).
  The vocabulary mirrors what Substack, Medium and the Guardian's renderer already have.
- The **hero** (the first image, under the title) is landscape at column width, or an
  inset. A square or portrait image at column width is drawn taller than a laptop
  screen, which is the complaint this module exists to answer.
- A body image that is square or portrait is an inset; a landscape one, a diagram or a
  chart is ``normal``. Few images: after the hero, at most one per 500-1000 words.
- Captions are one line, not italic (the platforms draw them small, centred, upright).

The class lives in the essay's front matter, out of the Markdown that goes to the
publisher::

    images:
      img/hero.png: inset

A GitHub comment honours it as ``<img width>``; python-substack honours it through its
own ``<!-- python-substack-image:v1 ... -->`` marker, which :func:`substack_markdown`
writes after each sized image. Neither ``{width=...}`` nor ``<img>`` may go to
python-substack (the first turns the image into its alt text, the second drops it).

>>> sizes_from_fields({"images": {"img/a.png": "inset"}})
{'img/a.png': 'inset'}
>>> suggest_size(1024, 1024, hero=True)
('inset', 'square hero: at column width it is taller than a laptop screen')
>>> suggest_size(1456, 819, hero=True)
('normal', 'landscape hero (16:9) fits the column')
"""

from __future__ import annotations

import base64
import json
import re
import struct
from pathlib import Path
from typing import Any, Iterator

from penult.base import PenultError
from penult.render import _IMAGE, _relative, essay_fields, local_images

__all__ = [
    "COLUMN_WIDTH",
    "DEFAULT_SIZE",
    "GITHUB_ATTRS",
    "INSET_WIDTH",
    "SIZES",
    "SUBSTACK_ATTRS",
    "describe_images",
    "github_attrs",
    "pixel_size",
    "sizes_from_fields",
    "substack_markdown",
    "suggest_size",
    "with_sizes",
]

#: The size classes, narrowest first.
SIZES = ("inset", "normal", "large", "full")
DEFAULT_SIZE = "normal"
#: Substack's post column, in CSS pixels (measured; the research report, section 2).
COLUMN_WIDTH = 728
#: An inset's rendered width, in CSS pixels, on both renderers: a little over half the
#: column, inside the Guardian's "supporting" range and Wikipedia's 400 px ceiling.
INSET_WIDTH = 400
#: Width/height ratio from which an image counts as landscape.
_LANDSCAPE = 1.3
#: After the hero, one body image per this many words is plenty.
WORDS_PER_IMAGE = 500

#: ``<img>`` attributes per class for a GitHub comment (the comment is already about
#: the column's width, so only ``inset`` narrows anything).
GITHUB_ATTRS: dict[str, dict[str, Any]] = {
    "inset": {"width": INSET_WIDTH},
    "normal": {},
    "large": {},
    "full": {},
}
#: ``image2`` attributes per class for python-substack. ``resizeWidth`` is what the
#: editor's own resize handle writes. ``large`` and ``full`` are the values the
#: stylesheet's ``sizing-large`` / ``sizing-fullscreen`` classes imply; a draft sized
#: in the editor and read back would confirm them (the report's open item).
SUBSTACK_ATTRS: dict[str, dict[str, Any]] = {
    "inset": {"resizeWidth": INSET_WIDTH},
    "normal": {},
    "large": {"imageSize": "large"},
    "full": {"fullscreen": True},
}


def sizes_from_fields(fields: dict) -> dict[str, str]:
    """The ``images:`` front-matter map, validated: relative path -> size class.

    >>> sizes_from_fields({})
    {}
    >>> sizes_from_fields({"images": {"img/a.png": "huge"}})
    Traceback (most recent call last):
    ...
    penult.base.PenultError: images: img/a.png: unknown size 'huge'; one of inset, normal, large, full
    """
    raw = fields.get("images") or {}
    if not isinstance(raw, dict):
        raise PenultError("images: must be a map of image path to size class")
    sizes: dict[str, str] = {}
    for path, size in raw.items():
        if size not in SIZES:
            raise PenultError(
                f"images: {path}: unknown size {size!r}; one of {', '.join(SIZES)}"
            )
        sizes[_relative(str(path))] = size
    return sizes


def github_attrs(size: str | None, *, inset_width: int = INSET_WIDTH) -> dict[str, Any]:
    """The ``<img>`` attributes a size class adds in a GitHub comment."""
    attrs = dict(GITHUB_ATTRS.get(size or DEFAULT_SIZE, {}))
    if "width" in attrs:
        attrs["width"] = inset_width
    return attrs


def _substack_attrs(size: str, *, inset_width: int) -> dict[str, Any]:
    attrs = dict(SUBSTACK_ATTRS.get(size, {}))
    if "resizeWidth" in attrs:
        attrs["resizeWidth"] = inset_width
    return attrs


def _marker(attrs: dict[str, Any]) -> str:
    payload = json.dumps(attrs, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"<!-- python-substack-image:v1 {encoded} -->"


def substack_markdown(
    markdown: str, sizes: dict[str, str] | None = None, *, inset_width: int = INSET_WIDTH
) -> str:
    """The essay with a python-substack image marker after each image whose class says so.

    The marker is an HTML comment python-substack merges into the ``image2`` node;
    GitHub and every Markdown viewer hide it. Front matter and the image lines are
    unchanged, so ``article``'s checks apply as before.

    >>> out = substack_markdown('---\\ntitle: T\\nimages:\\n  img/a.png: inset\\n---\\n# T\\n\\n![a](img/a.png "c")\\n')
    >>> out.splitlines()[-1].startswith("<!-- python-substack-image:v1 ")
    True
    """
    if sizes is None:
        sizes = sizes_from_fields(essay_fields(markdown))

    def mark(found: re.Match) -> str:
        src = _relative(found.group("src"))
        attrs = _substack_attrs(sizes.get(src, DEFAULT_SIZE), inset_width=inset_width)
        return found.group(0) + ("\n" + _marker(attrs) if attrs else "")

    return _IMAGE.sub(mark, markdown)


def pixel_size(path: Path) -> tuple[int, int] | None:
    """``(width, height)`` of a PNG, GIF or JPEG from its header, else ``None``."""
    try:
        with open(path, "rb") as f:
            head = f.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", head[16:24])
            if head[:6] in (b"GIF87a", b"GIF89a"):
                return struct.unpack("<HH", head[6:10])
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if marker[1] in (0xC0, 0xC1, 0xC2):
                        f.read(3)
                        h, w = struct.unpack(">HH", f.read(4))
                        return w, h
                    (length,) = struct.unpack(">H", f.read(2))
                    f.seek(length - 2, 1)
    except OSError:
        return None
    return None


def suggest_size(width: int, height: int, *, hero: bool) -> tuple[str, str]:
    """The size class the rules give an image of these pixels, with the reason.

    >>> suggest_size(709, 195, hero=False)
    ('normal', 'landscape (3.6:1) at column width')
    >>> suggest_size(700, 556, hero=False)
    ('inset', 'squarish (1.3:1): an inset keeps the text in view')
    """
    ratio = width / height if height else 1.0
    shape = f"{ratio:.1f}:1" if ratio >= 1 else f"1:{1 / ratio:.1f}"
    if ratio >= 1.75:
        shape = "16:9" if 1.7 <= ratio <= 1.85 else shape
    if hero:
        if ratio >= _LANDSCAPE:
            return "normal", f"landscape hero ({shape}) fits the column"
        kind = "square" if 0.9 <= ratio <= 1.1 else "portrait" if ratio < 0.9 else "squarish"
        return "inset", f"{kind} hero: at column width it is taller than a laptop screen"
    if ratio >= _LANDSCAPE:
        return "normal", f"landscape ({shape}) at column width"
    kind = "square" if 0.9 <= ratio <= 1.1 else "portrait" if ratio < 0.9 else "squarish"
    return "inset", f"{kind} ({shape}): an inset keeps the text in view"


def describe_images(folder: Path, markdown: str) -> Iterator[dict[str, Any]]:
    """One record per image: path, pixels, the class set, the class suggested, the reason."""
    fields = essay_fields(markdown)
    sizes = sizes_from_fields(fields)
    body = fields["content_markdown"]
    words = len(body.split())
    for i, src in enumerate(local_images(markdown)):
        pixels = pixel_size(folder / src)
        if pixels:
            suggested, reason = suggest_size(*pixels, hero=i == 0)
        else:
            suggested, reason = DEFAULT_SIZE, "file not found or not PNG/GIF/JPEG"
        yield {
            "image": src,
            "pixels": list(pixels) if pixels else None,
            "hero": i == 0,
            "size": sizes.get(src),
            "suggested": suggested,
            "reason": reason,
        }
    yield from _density_note(len(local_images(markdown)), words)


def _density_note(count: int, words: int) -> Iterator[dict[str, Any]]:
    body_images = max(count - 1, 0)
    if body_images and words / body_images < WORDS_PER_IMAGE:
        yield {
            "note": (
                f"{body_images} body image(s) for {words} words: fewer than one per "
                f"{WORDS_PER_IMAGE} words; each image needs its own purpose"
            )
        }


_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def with_sizes(markdown: str, sizes: dict[str, str]) -> str:
    """The essay text with its ``images:`` front-matter map replaced by ``sizes``.

    Only the ``images`` key changes; the other front-matter lines are kept as written.

    >>> print(with_sizes('---\\ntitle: T\\n---\\nbody\\n', {"img/a.png": "inset"}))
    ---
    title: T
    images:
      img/a.png: inset
    ---
    body
    <BLANKLINE>
    """
    found = _FRONT.match(markdown)
    if not found:
        raise PenultError("essay.md has no front matter to put the image sizes in")
    lines = found.group(1).split("\n")
    kept: list[str] = []
    skipping = False
    for line in lines:
        if re.match(r"^images:\s*(\{.*\})?\s*$", line):
            skipping = True
            continue
        if skipping and (line.startswith(" ") or line.startswith("\t")):
            continue
        skipping = False
        kept.append(line)
    block = [k for k, v in sizes.items() if v != DEFAULT_SIZE]
    if block:
        kept.append("images:")
        kept += [f"  {json.dumps(k)}: {sizes[k]}" if ":" in k or " " in k else f"  {k}: {sizes[k]}" for k in block]
    return "---\n" + "\n".join(kept) + "\n---\n" + markdown[found.end():]
