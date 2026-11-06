"""Where penult's private data lives, and the preferences read from it.

Everything a person tells penult about how they want their drafts made is private:
which voices, which platform, how many paid images, where their publishing
credentials are. None of it belongs in a repository. It lives under the data root::

    <data root>/config/preferences.json

The data root is the ``data_dir`` argument, else ``$PENULT_DATA_DIR``, else
``~/.local/share/penult`` (``$XDG_DATA_HOME`` and ``%LOCALAPPDATA%`` are honoured).

Code reaches the files through a ``MutableMapping`` of relative path to text, so the
local folder can be swapped for any other store (or a plain dict in tests) without
touching the rest:

>>> prefs = preferences(files={})
>>> prefs["max_generated_images"], prefs["platform"]
(2, 'substack')
>>> files = {}
>>> set_preference("platform", "medium", files=files)["platform"]
'medium'
>>> preferences(files=files)["platform"]
'medium'
"""

from __future__ import annotations

import json
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from penult.base import APP_NAME, DATA_DIR_ENVVAR, PenultError

__all__ = [
    "DEFAULT_PREFERENCES",
    "data_dir",
    "preferences",
    "set_preference",
    "text_files",
    "write_preferences",
]

_PREFERENCES_KEY = "config/preferences.json"

#: The preferences every verb falls back to. A person changes them with
#: ``penult prefs-set``; an agent changes them only when the person said so.
DEFAULT_PREFERENCES: dict[str, Any] = {
    # The penlike models the style pass writes with. The first is the base voice; the
    # author-choice guide (``penlike guide``) says which others fit a given essay.
    "voice_models": ["me"],
    "voice_register": "essay",
    "audience": "non-technical readers, or software engineers, managers and scientists",
    # Where ``publish`` sends the approved draft: substack (an unpublished draft via
    # the ``article`` package) or medium (article's Import-a-story step).
    "platform": "substack",
    # Paid image generation is capped; prompts beyond the cap are kept for the person
    # to try by hand.
    "max_generated_images": 2,
    "min_image_prompts": 5,
    # The ``article`` package's credentials and state, outside every repository.
    "article_env_file": "~/.config/article/.env",
    "article_state_path": "~/.local/share/article/pipeline_state.json",
    # Where a workspace goes inside the issue's repository checkout; ``{slug}`` is
    # derived from the issue title.
    "workspace": "docs/{slug}",
    "research_depth": "deep",
}


def data_dir(data_dir: str | os.PathLike | None = None) -> Path:
    """The data root: the argument, else ``$PENULT_DATA_DIR``, else the user data folder.

    >>> data_dir("somewhere").is_absolute()
    True
    """
    if data_dir:
        return Path(os.path.abspath(os.path.expanduser(str(data_dir))))
    configured = os.environ.get(DATA_DIR_ENVVAR)
    if configured:
        path = Path(os.path.expanduser(configured))
        if not path.is_absolute():
            raise PenultError(f"${DATA_DIR_ENVVAR} must be an absolute path, got {configured!r}")
        return path
    if os.name == "nt":  # pragma: no cover - exercised on Windows CI only
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def text_files(root: str | os.PathLike) -> MutableMapping[str, str]:
    """A ``dol`` files store under ``root``: ``/``-separated keys, UTF-8 text values.

    Folders are made on write and never on read, and a delete is permanent.
    """
    from dol import Files, mk_dirs_if_missing, wrap_kvs

    files = mk_dirs_if_missing(Files(str(root), delete_func=os.remove))
    return wrap_kvs(
        files,
        key_of_id=lambda k: k.replace(os.sep, "/"),
        id_of_key=lambda k: k.replace("/", os.sep),
        obj_of_data=lambda b: b.decode("utf-8", errors="replace"),
        data_of_obj=lambda s: s.encode("utf-8"),
    )


def _files(files: MutableMapping[str, str] | None, root: Any) -> MutableMapping[str, str]:
    return text_files(data_dir(root)) if files is None else files


def preferences(
    *, data_dir: Any = None, files: MutableMapping[str, str] | None = None
) -> dict[str, Any]:
    """The preferences: the defaults, overlaid with what the person wrote."""
    files = _files(files, data_dir)
    saved = json.loads(files[_PREFERENCES_KEY]) if _PREFERENCES_KEY in files else {}
    if not isinstance(saved, dict):
        raise PenultError(f"{_PREFERENCES_KEY} must hold a JSON object")
    return {**DEFAULT_PREFERENCES, **saved}


def write_preferences(
    values: dict[str, Any],
    *,
    data_dir: Any = None,
    files: MutableMapping[str, str] | None = None,
) -> None:
    """Replace the saved preferences (only the keys that differ from the defaults are kept)."""
    saved = {k: v for k, v in values.items() if DEFAULT_PREFERENCES.get(k, object()) != v}
    _files(files, data_dir)[_PREFERENCES_KEY] = json.dumps(saved, indent=2) + "\n"


def set_preference(
    key: str,
    value: Any,
    *,
    data_dir: Any = None,
    files: MutableMapping[str, str] | None = None,
) -> dict[str, Any]:
    """Set one preference and return the whole set.

    ``value`` is parsed as JSON when it is a string that parses (so ``2`` is a number
    and ``'["me", "dfw"]'`` a list), else kept as text.
    """
    if key not in DEFAULT_PREFERENCES:
        known = ", ".join(sorted(DEFAULT_PREFERENCES))
        raise PenultError(f"unknown preference {key!r}; the preferences are: {known}")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            pass
    current = preferences(data_dir=data_dir, files=files)
    current[key] = value
    write_preferences(current, data_dir=data_dir, files=files)
    return current
