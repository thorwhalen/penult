"""Errors, constants and the stage names shared across penult.

penult takes a seed (a GitHub issue) to a publication draft posted for review. The
stages below name where a workspace stands; every verb reads and advances them
through the workspace state file, and nothing here depends on any other module.
"""

from __future__ import annotations

APP_NAME = "penult"
DATA_DIR_ENVVAR = "PENULT_DATA_DIR"

#: A seed with fewer words than this (title, body and comments together) is "thin":
#: the agent asks the user where to take it before researching or drafting.
THIN_SEED_WORDS = 250

#: The stages a workspace moves through, in order. ``approved`` is set by the user
#: (or by the agent relaying the user's words) and gates ``published``.
STAGES = (
    "seeded",
    "researched",
    "drafted",
    "styled",
    "illustrated",
    "posted",
    "approved",
    "published",
)

STATE_FILE = "penult.json"
SEED_FILE = "seed.md"
BRIEF_FILE = "brief.md"
ESSAY_FILE = "essay.md"
IMAGES_FILE = "images.md"
COMMENT_FILE = "comment.md"
CHECK_FILE = "check.md"
IMG_DIR = "img"
RESEARCH_DIR = "research"


class PenultError(Exception):
    """An error whose message says what to do next."""


def stage_index(stage: str) -> int:
    """Where a stage sits in :data:`STAGES`; unknown stages sort first.

    >>> stage_index("drafted") > stage_index("seeded")
    True
    """
    return STAGES.index(stage) if stage in STAGES else -1
