"""One essay's workspace: its files, its state, and the seed and brief written into it.

A workspace is a folder, by default ``docs/<slug>/`` inside the issue's repository,
so that the research notes, the essay and its images are versioned next to the
issue they came from and found by whoever indexes that repository's docs::

    <workspace>/
        penult.json      state: the issue, the stage, the images, the comment, the draft
        seed.md          the issue as fetched: title, body, comments
        brief.md         angle, audience, voice, platform, image budget, assumptions
        research/        the research notes (Vancouver references), one file per theme
        essay.md         the draft, with front matter for title and subtitle
        images.md        every image candidate and prompt, with credit and licence
        img/             the images the essay uses
        comment.md       the essay rendered for an issue comment
        check.md         the last style and machine-writing check

>>> ws = Workspace("/tmp/x/docs/an-essay")
>>> ws.essay.name, ws.state_file.name
('essay.md', 'penult.json')
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from penult.base import (
    BRIEF_FILE,
    CHECK_FILE,
    COMMENT_FILE,
    ESSAY_FILE,
    IMAGES_FILE,
    IMG_DIR,
    RESEARCH_DIR,
    SEED_FILE,
    STATE_FILE,
    THIN_SEED_WORDS,
    PenultError,
    stage_index,
)

__all__ = ["Workspace", "is_thin", "slug_of", "word_count"]


def now() -> str:
    """The current UTC time, to the second, as ISO 8601."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def word_count(text: str) -> int:
    """How many whitespace-separated words a text has.

    >>> word_count("one two  three\\nfour")
    4
    """
    return len(text.split())


def slug_of(title: str, *, max_length: int = 60) -> str:
    """A folder-safe slug from a title, cut at a word boundary.

    >>> slug_of("AI and the Accretion Trap: Why Experts Underestimate Broken Technologies")
    'ai-and-the-accretion-trap-why-experts-underestimate-broken'
    """
    words = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-").split("-")
    out: list[str] = []
    for word in words:
        if out and len("-".join(out + [word])) > max_length:
            break
        out.append(word)
    return "-".join(out) or "essay"


def is_thin(issue: dict[str, Any], *, threshold: int = THIN_SEED_WORDS) -> dict[str, Any]:
    """Whether the seed is too thin to research and draft from without asking.

    A thin seed is one with fewer than ``threshold`` words in title, body and
    comments together. The result says why, so the agent can quote it in the
    questions it sends.

    >>> is_thin({"title": "An idea", "body": "Agents read specs.", "comments": []})["thin"]
    True
    """
    texts = [issue.get("title", ""), issue.get("body", "")]
    texts += [c.get("body", "") for c in issue.get("comments") or []]
    words = sum(word_count(t) for t in texts)
    has_thesis = bool(re.search(r"[.!?]\s", issue.get("body", "") + " "))
    thin = words < threshold or not has_thesis
    reasons = []
    if words < threshold:
        reasons.append(f"{words} words in the seed, under the {threshold} it takes to draft from")
    if not has_thesis:
        reasons.append("no full sentence in the body: no thesis to argue")
    return {"thin": thin, "words": words, "reasons": reasons}


class Workspace:
    """The folder of one essay and the files in it."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder).expanduser().resolve()

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Workspace({str(self.folder)!r})"

    # -- paths ----------------------------------------------------------------------
    @property
    def state_file(self) -> Path:
        """The state file."""
        return self.folder / STATE_FILE

    seed = property(lambda self: self.folder / SEED_FILE)
    brief = property(lambda self: self.folder / BRIEF_FILE)
    essay = property(lambda self: self.folder / ESSAY_FILE)
    images_ledger = property(lambda self: self.folder / IMAGES_FILE)
    comment = property(lambda self: self.folder / COMMENT_FILE)
    check_report = property(lambda self: self.folder / CHECK_FILE)
    img = property(lambda self: self.folder / IMG_DIR)
    research = property(lambda self: self.folder / RESEARCH_DIR)

    def exists(self) -> bool:
        """Whether this folder was started by penult."""
        return self.state_file.is_file()

    def require(self) -> Workspace:
        """This workspace, or an error saying how to start one."""
        if not self.exists():
            raise PenultError(
                f"{self.folder} is not a penult workspace (no {STATE_FILE}); "
                f"start one with: penult start <issue url>"
            )
        return self

    # -- state ----------------------------------------------------------------------
    def read_state(self) -> dict[str, Any]:
        """The state, ``{}`` before the workspace is started."""
        if not self.state_file.is_file():
            return {}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def write_state(self, state: dict[str, Any]) -> None:
        """Replace the state."""
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def update_state(self, **changes: Any) -> dict[str, Any]:
        """Merge ``changes`` into the state and return it."""
        state = self.read_state()
        state.update(changes)
        state["updated"] = now()
        self.write_state(state)
        return state

    def advance(self, stage: str) -> dict[str, Any]:
        """Move to ``stage`` unless the workspace is already past it."""
        state = self.read_state()
        if stage_index(stage) >= stage_index(state.get("stage", "")):
            state["stage"] = stage
            state["updated"] = now()
            self.write_state(state)
        return state

    # -- what the files say ----------------------------------------------------------
    def files_present(self) -> dict[str, Any]:
        """Which of the expected files exist, with word counts where that means something."""
        research = sorted(p.name for p in self.research.glob("*.md")) if self.research.is_dir() else []
        images = sorted(p.name for p in self.img.iterdir() if p.is_file()) if self.img.is_dir() else []
        essay_words = word_count(self.essay.read_text(encoding="utf-8")) if self.essay.is_file() else 0
        return {
            "seed": self.seed.is_file(),
            "brief": self.brief.is_file(),
            "research": research,
            "essay": self.essay.is_file(),
            "essay_words": essay_words,
            "images_ledger": self.images_ledger.is_file(),
            "images": images,
            "comment": self.comment.is_file(),
            "check": self.check_report.is_file(),
        }


def seed_markdown(issue: dict[str, Any]) -> str:
    """The issue as a Markdown file: title, provenance, body, then each comment."""
    lines = [
        f"# {issue.get('title', '').strip()}",
        "",
        f"Seed: {issue.get('url', '')} (by {issue.get('author') or 'unknown'}, {issue.get('created', '')[:10]}). "
        f"Fetched {now()[:10]} by penult. This file is the point of departure, kept as it was.",
        "",
        "## Body",
        "",
        issue.get("body", "").rstrip(),
        "",
    ]
    for i, comment in enumerate(issue.get("comments") or [], start=1):
        lines += [
            f"## Comment {i} by {comment.get('author') or 'unknown'} ({comment.get('created', '')[:10]})",
            "",
            comment.get("body", "").rstrip(),
            "",
        ]
    return "\n".join(lines)


def brief_markdown(issue: dict[str, Any], prefs: dict[str, Any], thin: dict[str, Any]) -> str:
    """The brief the agent fills before researching: angle, audience, voice, images, platform.

    Lines marked ``[DECIDE: ...]`` are the agent's to settle (with the user when the
    seed is thin, from the seed and these preferences otherwise), and the decisions
    stay here so a later session can see what was assumed.
    """
    voice = ", ".join(prefs.get("voice_models") or ["me"])
    verdict = (
        "THIN: ask the user first (" + "; ".join(thin["reasons"]) + "), with a recommendation for each question."
        if thin["thin"]
        else f"rich enough ({thin['words']} words): decide the open lines below from the seed and record the assumptions."
    )
    return "\n".join(
        [
            f"# Brief: {issue.get('title', '').strip()}",
            "",
            f"Seed: {issue.get('url', '')}. Seed verdict: {verdict}",
            "",
            "## What the essay argues",
            "",
            "[DECIDE: the thesis in one or two sentences, in the author's words where the seed has them]",
            "",
            "## Angle and shape",
            "",
            "[DECIDE: what the essay is (an argument, a story and its moral, a debunking, a field guide), its length, and what it is not: never a report unless asked]",
            "",
            "## Audience",
            "",
            f"{prefs.get('audience', '')} [DECIDE: narrow this for this essay]",
            "",
            "## Voice",
            "",
            f"Base voice: `{voice}` (penlike register `{prefs.get('voice_register', 'essay')}`). "
            "Other authors: chosen with `penlike guide` for this subject. [DECIDE: which, for which passages]",
            "",
            "## Research",
            "",
            f"Depth: {prefs.get('research_depth', 'deep')}. Every claim in the seed is checked; critiques and counter-evidence are gathered so the essay knows both sides; "
            "candidate figures, tables and images are indexed with their licence. Notes go in `research/`, Vancouver references, never in the essay's format.",
            "",
            "## Images",
            "",
            f"At least {prefs.get('min_image_prompts', 5)} prompts written to `images.md`; at most {prefs.get('max_generated_images', 2)} generated automatically; stock and public-domain candidates found with `illustration`, credited. "
            "[DECIDE: the visual style, if the seed or the user says]",
            "",
            "## Platform",
            "",
            f"Default: {prefs.get('platform', 'substack')} (an unpublished draft, after the user approves the issue-comment draft). [DECIDE: keep or change]",
            "",
            "## Assumptions and questions",
            "",
            "[the agent's assumptions, and the questions it asked the user, with the answers]",
            "",
        ]
    )
