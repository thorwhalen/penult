"""penult: from an idea to a publication draft, posted where its author can review it.

The seed is a GitHub issue. penult fetches it into a workspace next to it, holds the
brief, the research notes, the essay, the images and their credits, checks the draft
with ductus and penlike, renders it as an issue comment, and, once the author says
so, hands it to ``article`` for an unpublished Substack or Medium draft. The
thinking in between (research, drafting, the style passes) is an agent's, laid out
in the ``penult`` skill; the verbs here keep every step from being improvised twice.

>>> import penult
>>> penult.prefs(files={})["preferences"]["platform"]
'substack'
"""

from penult.base import STAGES, PenultError
from penult.store import DEFAULT_PREFERENCES, data_dir, preferences
from penult.tools import (
    TOOLS,
    approve,
    check,
    image_add,
    image_generate,
    image_search,
    layout,
    mark,
    post,
    prefs,
    prefs_set,
    publish,
    render,
    start,
    status,
)
from penult.workspace import Workspace

__all__ = [
    "DEFAULT_PREFERENCES",
    "STAGES",
    "TOOLS",
    "PenultError",
    "Workspace",
    "approve",
    "check",
    "data_dir",
    "image_add",
    "image_generate",
    "image_search",
    "layout",
    "mark",
    "post",
    "preferences",
    "prefs",
    "prefs_set",
    "publish",
    "render",
    "start",
    "status",
]
