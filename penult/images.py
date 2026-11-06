"""Images for the essay: find existing ones, generate a few, and keep the ledger.

Three sources, one ledger (``images.md`` in the workspace, mirrored in the state):

- **search**: existing stock, Creative-Commons and public-domain images through the
  ``illustration`` package, which carries licence and attribution with each hit;
- **generate**: a paid image from a prompt through ``aix.image.generate_image``,
  capped by the person's ``max_generated_images`` so that an off prompt does not
  cost much; every prompt is kept in the ledger whether or not it was run;
- **add**: an image the person made or found themselves, with its credit.

The searcher and the generator are seams: any callable of the same shape works, and
tests pass fakes.

>>> credit_line({"title": "Harbour", "author": "A. Painter", "license": "cc-by", "source": "openverse"})
'Harbour, by A. Painter (cc-by, via openverse)'
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Any, Callable

from penult.base import PenultError
from penult.workspace import Workspace, now

__all__ = ["add_image", "credit_line", "default_generator", "default_searcher", "generate_image", "search_images"]

_LEDGER_HEADER = (
    "# Images\n\n"
    "Every candidate, prompt and image for this essay, with its credit. Generated images are "
    "capped by the author's preferences; prompts past the cap are here to try by hand.\n\n"
    "| when | kind | file or URL | credit / prompt | licence | used |\n|---|---|---|---|---|---|\n"
)


def _hit_field(hit: Any, *names: str) -> Any:
    for name in names:
        value = getattr(hit, name, None)
        if value is None and isinstance(hit, dict):
            value = hit.get(name)
        if value:
            return value
    return None


def hit_record(hit: Any) -> dict[str, Any]:
    """One search hit as a plain dict, whatever object the searcher returned."""
    return {
        "url": _hit_field(hit, "url", "image_url"),
        "page": _hit_field(hit, "source_page_url", "page_url", "foreign_landing_url", "source_url", "landing_url"),
        "title": _hit_field(hit, "title", "alt", "description") or "",
        "author": _hit_field(hit, "author", "creator", "photographer") or "",
        "license": _hit_field(hit, "license", "license_type") or "",
        "attribution": _hit_field(hit, "attribution") or "",
        "source": _hit_field(hit, "source", "provider") or "",
        "cacheable": _hit_field(hit, "cacheable"),
    }


def credit_line(record: dict[str, Any]) -> str:
    """A one-line credit from a record: the attribution if the source gave one, else built."""
    if record.get("attribution"):
        return str(record["attribution"])
    title = record.get("title") or "Untitled"
    by = f", by {record['author']}" if record.get("author") else ""
    tail = ", ".join(x for x in (record.get("license"), f"via {record['source']}" if record.get("source") else "") if x)
    return f"{title}{by}" + (f" ({tail})" if tail else "")


def default_searcher(query: str, *, n: int = 8, **options: Any) -> list[Any]:
    """The ``illustration`` package's unified search (Openverse by default, no key needed)."""
    try:
        import illustration
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise PenultError("image search needs the illustration package: pip install 'penult[images]'") from error
    return list(illustration.search(query, n=n, **options))


def default_generator(prompt: str, *, path: Path, **options: Any) -> Path:
    """Generate one image with ``aix`` (DALL-E 3 and other litellm providers) and save it."""
    try:
        from aix.image import generate_image
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise PenultError("image generation needs aix with litellm: pip install 'penult[images]'") from error
    image = generate_image(prompt, **options)
    image.save(path)
    return path


def _append_ledger(ws: Workspace, row: dict[str, Any]) -> None:
    ws.folder.mkdir(parents=True, exist_ok=True)
    if not ws.images_ledger.is_file():
        ws.images_ledger.write_text(_LEDGER_HEADER, encoding="utf-8")
    cells = [
        row.get("when", "")[:16],
        row.get("kind", ""),
        row.get("file") or row.get("url") or "",
        (row.get("prompt") or row.get("credit") or "").replace("|", "/"),
        row.get("license") or "",
        "yes" if row.get("used") else "",
    ]
    with ws.images_ledger.open("a", encoding="utf-8") as f:
        f.write("| " + " | ".join(str(c).replace("\n", " ") for c in cells) + " |\n")
    state = ws.read_state()
    state.setdefault("images", []).append(row)
    ws.write_state(state)


def _rejected(error: Exception) -> bool:
    """Whether an error is the provider refusing the request (HTTP 4xx), which is never billed.

    >>> class E(Exception): status_code = 400
    >>> _rejected(E()), _rejected(ValueError("Error code: 404 - no such model")), _rejected(RuntimeError("timeout"))
    (True, True, False)
    """
    code = getattr(error, "status_code", None) or getattr(getattr(error, "response", None), "status_code", None)
    if isinstance(code, int):
        return 400 <= code < 500
    found = re.search(r"error code:?\s*(\d{3})\b", str(error), re.IGNORECASE)
    return bool(found) and 400 <= int(found.group(1)) < 500


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    if not cleaned or cleaned.startswith("."):
        raise PenultError(f"{name!r} is not a usable file name")
    return cleaned


def search_images(
    ws: Workspace, query: str, *, n: int = 8, searcher: Callable[..., list[Any]] | None = None, **options: Any
) -> list[dict[str, Any]]:
    """Find existing images for ``query`` and record the candidates in the ledger."""
    searcher = searcher or default_searcher
    hits = [hit_record(h) for h in searcher(query, n=n, **options)]
    for hit in hits:
        _append_ledger(ws, {
            "when": now(), "kind": "candidate", "url": hit["url"], "page": hit["page"],
            "credit": credit_line(hit), "license": hit["license"], "query": query, "used": False,
        })  # fmt: skip
    return hits


def add_image(
    ws: Workspace, source: str, *, name: str, credit: str, license: str = "", prompt: str | None = None, used: bool = True
) -> Path:
    """Put an image in ``img/`` (from a URL or a local path) and record its credit."""
    name = _safe_name(name)
    ws.img.mkdir(parents=True, exist_ok=True)
    suffix = Path(source.split("?")[0]).suffix or ".png"
    target = ws.img / (name if Path(name).suffix else name + suffix)
    if re.match(r"https?://", source):
        # Wikimedia and others refuse urllib's default agent; name ourselves.
        request = urllib.request.Request(source, headers={"User-Agent": "penult/0.1 (+https://github.com/thorwhalen/penult)"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - the user's own URL
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
        except OSError as error:
            raise PenultError(f"could not download {source}: {error}") from error
        if not Path(source.split("?")[0]).suffix and not Path(name).suffix:
            guessed = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp", "image/svg+xml": ".svg"}
            target = target.with_suffix(guessed.get(content_type.split(";")[0].strip(), ".png"))
        target.write_bytes(data)
    else:
        origin = Path(source).expanduser()
        if not origin.is_file():
            raise PenultError(f"no such image file: {source}")
        if origin.resolve() != target.resolve():
            target.write_bytes(origin.read_bytes())
    _append_ledger(ws, {
        "when": now(), "kind": "generated-by-hand" if prompt else "added", "file": f"img/{target.name}",
        "credit": credit, "license": license, "prompt": prompt,
        "origin": source if re.match(r"https?://", source) else None, "used": used,
    })  # fmt: skip
    return target


def generate_image(
    ws: Workspace,
    prompt: str,
    *,
    name: str,
    max_generated: int,
    force: bool = False,
    generator: Callable[..., Path] | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Generate one image from ``prompt`` into ``img/``, within the budget.

    The budget counts images this workspace generated automatically. Past it, the
    prompt is recorded for the person to try by hand and nothing is spent, unless
    ``force`` is set (the person asked for this one).
    """
    name = _safe_name(name)
    state = ws.read_state()
    generated = [r for r in state.get("images", []) if r.get("kind") in ("generated", "generated-failed")]
    if len(generated) >= max_generated and not force:
        _append_ledger(ws, {"when": now(), "kind": "prompt", "prompt": prompt, "used": False})
        return {
            "generated": False,
            "prompt": prompt,
            "reason": f"budget of {max_generated} automatic image(s) spent; prompt recorded in images.md (use --force to spend one more)",
        }
    ws.img.mkdir(parents=True, exist_ok=True)
    target = ws.img / (name if Path(name).suffix else name + ".png")
    try:
        path = (generator or default_generator)(prompt, path=target, **options)
    except Exception as error:
        # A request the provider rejected (a 4xx: bad parameter, unknown model) was
        # never billed and does not count; anything else may have been, and does.
        kind = "generation-error" if _rejected(error) else "generated-failed"
        _append_ledger(ws, {"when": now(), "kind": kind, "prompt": prompt, "credit": str(error)[:200], "used": False})
        raise
    _append_ledger(ws, {
        "when": now(), "kind": "generated", "file": f"img/{Path(path).name}", "prompt": prompt,
        "credit": "Image generated for this essay", "license": "", "used": True,
    })  # fmt: skip
    return {"generated": True, "prompt": prompt, "file": f"img/{Path(path).name}"}
