"""The verbs: plain functions, JSON-ready in and out, the one list every surface is built from.

An agent drives an essay from a seed to a reviewed draft with these, in this order::

    start      fetch the seed (a GitHub issue), make the workspace, say whether it is thin
    status     where the workspace stands and what comes next
    mark       record a stage reached by the agent's own work (researched, drafted, ...)
    check      ductus and penlike over the essay: what still reads machine-made or off-voice
    image-search / image-generate / image-add   images, within the budget, all credited
    render     the essay as an issue comment, images as raw URLs pinned to the commit
    post       post (or update) that comment on the issue
    approve    record that the person is happy with the posted draft, as it was then
    publish    hand the approved essay to ``article`` for an unpublished platform draft
    prefs / prefs-set   the private preferences

The thinking (research, drafting, the style passes) is the agent's and is laid out
in the ``penult`` skill; these verbs hold the state, the files, the budget and the
hand-offs so that no step is improvised twice. Nothing here prints or exits: the
command line and any other surface wrap :data:`TOOLS`.
"""

from __future__ import annotations

import functools
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Callable

from penult import github as _gh
from penult import images as _images
from penult import figures as _layout
from penult.base import STAGES, PenultError
from penult.render import essay_fields, local_images, render_comment, text_hash
from penult.store import DEFAULT_PREFERENCES, data_dir, preferences, set_preference
from penult.workspace import (
    Workspace,
    brief_markdown,
    is_thin,
    now,
    seed_markdown,
    slug_of,
)

__all__ = ["HIDDEN_PARAMETERS", "TOOLS", "without"]

#: Parameters a surface built from these signatures leaves out: the in-memory store and
#: the injected callables are for Python callers and tests.
HIDDEN_PARAMETERS = ("files", "fetch", "runner", "searcher", "generator", "publisher")
_TIMEOUT = 600


def without(func: Callable, hidden=HIDDEN_PARAMETERS) -> Callable:
    """The same verb with ``hidden`` parameters removed from its signature.

    >>> "files" in inspect.signature(without(prefs)).parameters
    False
    """
    hidden = set(hidden)
    signature = inspect.signature(func)

    @functools.wraps(func)
    def verb(*args, **kwargs):
        return func(*args, **kwargs)

    verb.__signature__ = signature.replace(
        parameters=[p for p in signature.parameters.values() if p.name not in hidden]
    )
    return verb


def _ws(folder: str | None) -> Workspace:
    return Workspace(folder or os.getcwd()).require()


def _prefs(data_dir, files) -> dict[str, Any]:
    return preferences(data_dir=data_dir, files=files)


def _essay_text(ws: Workspace) -> str:
    if not ws.essay.is_file():
        raise PenultError(f"no {ws.essay.name} in {ws.folder} yet")
    return ws.essay.read_text(encoding="utf-8")


# -- start and status ------------------------------------------------------------------


def start(
    seed: str,
    *,
    into: str | None = None,
    force: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    fetch: Callable[..., dict] | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Fetch the seed (a GitHub issue URL) and make the workspace: seed, brief, state.

    The workspace goes ``into`` the folder given, else to the ``workspace`` preference
    (``docs/<slug>`` by default) inside the checkout of the issue's own repository
    that holds the current directory. A thin seed (few words, no thesis) is reported
    so the agent asks the user before researching. ``--force`` refetches the seed into
    an existing workspace; the brief and the stage are kept.
    """
    issue = (fetch or functools.partial(_gh.fetch_issue, runner=runner))(seed)
    prefs = _prefs(data_dir, files)
    slug = slug_of(issue["title"])
    if into:
        folder = Path(into).expanduser()
    else:
        checkout = _gh.repo_of_checkout(Path(os.getcwd()), runner=runner)
        same_repo = checkout and (checkout["owner"].lower(), checkout["repo"].lower()) == (
            issue["owner"].lower(), issue["repo"].lower(),
        )  # fmt: skip
        if not same_repo:
            raise PenultError(
                f"the current directory is not a checkout of {issue['owner']}/{issue['repo']}; "
                f"run from one, or say where the workspace goes with --into <folder>"
            )
        folder = Path(checkout["root"]) / prefs["workspace"].format(slug=slug)
    ws = Workspace(folder)
    if ws.exists() and not force:
        raise PenultError(
            f"{ws.folder} already holds a workspace; use --force to refetch the seed into it"
        )
    if (
        not ws.exists()
        and ws.folder.is_dir()
        and any(ws.folder.iterdir())
        and not force
    ):
        raise PenultError(
            f"{ws.folder} exists and is not a penult workspace; choose another --into, or --force"
        )
    thin = is_thin(issue)
    ws.folder.mkdir(parents=True, exist_ok=True)
    ws.seed.write_text(seed_markdown(issue), encoding="utf-8")
    if not ws.brief.is_file():
        ws.brief.write_text(brief_markdown(issue, prefs, thin), encoding="utf-8")
    ws.research.mkdir(exist_ok=True)
    ws.img.mkdir(exist_ok=True)
    state = ws.read_state()
    state.update(
        seed_kind=issue.get("kind", "github-issue"), issue=issue["url"], issue_title=issue["title"],
        repo=f"{issue['owner']}/{issue['repo']}", number=issue["number"], slug=slug,
        stage=state.get("stage") or "seeded", thin=thin["thin"], seed_words=thin["words"],
        platform=state.get("platform") or prefs["platform"], created=state.get("created") or now(), updated=now(),
    )  # fmt: skip
    state.setdefault("images", [])
    ws.write_state(state)
    verdict = (
        "THIN: ask the user before researching"
        if thin["thin"]
        else "rich enough: decide the brief and go on"
    )
    return {
        "ok": True,
        "summary": f"workspace {ws.folder} ({verdict})",
        "workspace": str(ws.folder),
        "slug": slug,
        "thin": thin,
        "files": {
            "seed": str(ws.seed),
            "brief": str(ws.brief),
            "state": str(ws.state_file),
        },
        "next": "fill brief.md (ask the user if thin), then research into research/, then write essay.md",
        "text": f"{ws.folder}\nseed: {thin['words']} words; {verdict}\n"
        + (
            "\n".join(f"  - {r}" for r in thin["reasons"]) + "\n"
            if thin["reasons"]
            else ""
        )
        + f"next: fill {ws.brief.name}, research into research/, write essay.md",
    }


def status(folder: str | None = None) -> dict:
    """Where the workspace stands: stage, files present, images, the posted comment, what comes next."""
    ws = _ws(folder)
    state = ws.read_state()
    present = ws.files_present()
    stage = state.get("stage", "seeded")
    nxt = {
        "seeded": "research (notes in research/), then write essay.md",
        "researched": "write essay.md from the brief and the research",
        "drafted": "style passes (penlike, ductus, deslop), then penult check",
        "styled": "images: penult image-search / image-generate / image-add, place them in essay.md",
        "illustrated": "commit and push the workspace, then penult render and penult post",
        "posted": "wait for the user's review; iterate; penult approve when they are happy",
        "approved": "penult publish",
        "published": "the user reviews the platform draft and publishes it by hand",
    }.get(stage, "")
    lines = [
        f"{state.get('issue', '')}: {state.get('issue_title', '')}",
        f"stage: {stage}  (stages: {' > '.join(STAGES)})",
        f"essay: {'%d words' % present['essay_words'] if present['essay'] else 'not written'}; "
        f"research notes: {len(present['research'])}; images in img/: {len(present['images'])}; "
        f"generated: {sum(1 for i in state.get('images', []) if i.get('kind') == 'generated')}",
    ]
    if state.get("comment_url"):
        lines.append(f"posted: {state['comment_url']}")
    for platform, url in (state.get("draft_urls") or {}).items():
        lines.append(f"{platform} draft: {url}")
    lines.append(f"next: {nxt}")
    return {
        "ok": True,
        "summary": f"{stage}",
        "state": state,
        "files": present,
        "next": nxt,
        "text": "\n".join(lines),
    }


def mark(folder: str | None = None, *, stage: str) -> dict:
    """Record that the workspace reached ``stage`` (researched, drafted, styled, illustrated)."""
    ws = _ws(folder)
    if stage not in STAGES:
        raise PenultError(f"unknown stage {stage!r}; one of: {', '.join(STAGES)}")
    if stage in ("posted", "approved", "published"):
        raise PenultError(
            f"{stage!r} is set by penult post / approve / publish, not by hand"
        )
    state = ws.advance(stage)
    return {"ok": True, "summary": f"stage {state['stage']}", "stage": state["stage"]}


# -- checks ----------------------------------------------------------------------------


def _tool_json(
    module: str, args: list[str], *, runner: Callable, stdin: str | None = None
) -> dict | None:
    """Run ``python -m <module> ...`` and parse its JSON; ``None`` when the module is not installed."""
    if importlib.util.find_spec(module) is None:
        return None
    done = runner(
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        input=stdin,
        timeout=_TIMEOUT,
    )
    out = (done.stdout or "").strip()
    if not out:
        return {"error": (done.stderr or "").strip()[:500]}
    try:
        return json.loads(out)
    except ValueError:
        return {"error": out[:500]}


def check(
    folder: str | None = None,
    *,
    like: list[str] | None = None,
    style: str | None = None,
    out: str | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Read the essay with ductus and penlike, and write what they found to a private check file.

    ductus marks the segments that read machine-made (lean toward +1, with the
    evidence strength); penlike measures the draft against each voice model in
    ``like`` (the ``voice_models`` preference by default). The report quotes figures
    from the author's private style models, so it goes under the data root
    (``work/<slug>/check.md``), not into the workspace, unless ``out`` says where.
    The agent's own reading comes on top of this; neither tool sees bland prose that
    carries no tell.
    """
    ws = _ws(folder)
    body = essay_fields(_essay_text(ws))["content_markdown"]
    prefs = _prefs(data_dir, files)
    like = like or prefs["voice_models"]
    style = style or prefs["voice_register"]
    report: dict[str, Any] = {"when": now(), "ductus": None, "penlike": {}}
    lines = [f"# Check of {ws.essay.name}, {now()[:16]}", ""]

    gauge = _tool_json(
        "ductus", ["gauge", "-", "--format", "json"], runner=runner, stdin=body
    )
    if gauge is None:
        lines += [
            "ductus: not installed (pip install ductus); the agent reads for machine-sounding passages alone.",
            "",
        ]
    elif "segments" not in gauge:
        lines += [f"ductus: failed: {gauge.get('error', gauge)}", ""]
    else:
        doc = gauge.get("document", {})
        flagged = sorted(
            (
                s
                for s in gauge["segments"]
                if (s.get("lean") or 0) > 0 and (s.get("strength") or 0) > 0
            ),
            key=lambda s: -(s.get("lean", 0) * s.get("strength", 0)),
        )
        report["ductus"] = {
            "label": doc.get("label"),
            "lean": doc.get("lean"),
            "strength": doc.get("strength"),
            "flagged": len(flagged),
        }
        lines += [
            f"## ductus: {doc.get('label')} (lean {doc.get('lean')}, strength {doc.get('strength')}); {len(flagged)} segment(s) lean machine",
            "",
        ]
        for seg in flagged[:25]:
            quote = (
                (seg.get("text") or (seg.get("span") or {}).get("quote") or "")
                .strip()
                .replace("\n", " ")
            )
            reasons = "; ".join(
                sig.get("note", "")
                for sig in seg.get("signals", [])[:2]
                if sig.get("direction") == "machine"
            )
            lines.append(
                f'- lean {seg.get("lean"):+.2f} / strength {seg.get("strength"):.2f}: "{quote[:160]}"'
                + (f" ({reasons})" if reasons else "")
            )
        lines.append("")

    for model in like:
        result = _tool_json(
            "penlike",
            ["check", "-", "--like", model, "--style", style, "--json"],
            runner=runner,
            stdin=body,
        )
        if result is None:
            lines += [
                "penlike: not installed (pip install penlike); voice not measured.",
                "",
            ]
            break
        if "discrepancies" not in result:
            lines += [
                f"## penlike against `{model}`: failed: {result.get('error', result)}",
                "",
            ]
            continue
        discrepancies = result["discrepancies"]
        report["penlike"][model] = {
            "register": result.get("register"),
            "discrepancies": len(discrepancies),
        }
        lines += [
            f"## penlike against `{model}` ({result.get('register')}): {len(discrepancies)} discrepancies",
            "",
        ]
        lines += [
            "- " + line.lstrip("- ").strip()
            for line in (result.get("text") or "").splitlines()
            if line.strip()
        ][:30]
        lines.append("")

    target = (
        Path(out).expanduser()
        if out
        else data_dir_path(data_dir) / "work" / ws.folder.name / "check.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    ws.update_state(
        last_check=report
    )  # the path is local and private; it is returned, not stored
    return {
        "ok": True,
        "summary": f"check written to {target}",
        "report": report,
        "path": str(target),
        "text": "\n".join(lines),
    }


def data_dir_path(data_dir_arg) -> Path:
    """The data root for the ``data_dir`` argument (``None`` means the configured default)."""
    return data_dir(data_dir_arg)


# -- images ----------------------------------------------------------------------------


def image_search(
    query: str,
    *,
    folder: str | None = None,
    n: int = 8,
    searcher: Callable | None = None,
) -> dict:
    """Find existing stock, Creative-Commons or public-domain images for ``query``, credited.

    Candidates are recorded in images.md. Download the one you use with
    ``image-add <url> --name <file> --credit "<the credit line shown>"``.
    """
    ws = _ws(folder)
    hits = _images.search_images(ws, query, n=n, searcher=searcher)
    lines = [
        f"{i}. {_images.credit_line(h)}\n   {h['url']}"
        + (f"\n   page: {h['page']}" if h.get("page") else "")
        for i, h in enumerate(hits, 1)
    ]
    return {
        "ok": True,
        "summary": f"{len(hits)} candidate(s) for {query!r}",
        "hits": hits,
        "text": "\n".join(lines) or "no candidates",
    }


def image_generate(
    prompt: str,
    *,
    name: str,
    folder: str | None = None,
    force: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    generator: Callable | None = None,
) -> dict:
    """Generate one image from ``prompt`` into img/, within the ``max_generated_images`` budget.

    Past the budget the prompt is only recorded in images.md, for the person to try
    by hand; ``--force`` spends one more because the person asked.
    """
    ws = _ws(folder)
    prefs = _prefs(data_dir, files)
    result = _images.generate_image(
        ws,
        prompt,
        name=name,
        max_generated=int(prefs["max_generated_images"]),
        force=force,
        generator=generator,
    )
    text = (
        f"generated {result['file']}"
        if result["generated"]
        else f"not generated: {result['reason']}"
    )
    return {"ok": True, "summary": text, **result, "text": text}


def image_add(
    source: str,
    *,
    name: str,
    credit: str,
    folder: str | None = None,
    license: str = "",
    prompt: str | None = None,
) -> dict:
    """Add an image (a URL or a local file) to img/ with its credit; ``--prompt`` if a person generated it."""
    ws = _ws(folder)
    path = _images.add_image(
        ws, source, name=name, credit=credit, license=license, prompt=prompt
    )
    rel = f"img/{path.name}"
    return {
        "ok": True,
        "summary": f"added {rel}",
        "file": rel,
        "markdown": f'![ALT]({rel} "{credit}")',
        "text": f'{rel}\n![ALT]({rel} "{credit}")',
    }


# -- layout ----------------------------------------------------------------------------


def layout(
    folder: str | None = None,
    *,
    apply: bool = False,
) -> dict:
    """Each image's size class against the layout rules; ``--apply`` writes the suggestions.

    The rules (``penult.figures``, from the layout research in ``misc/docs/research/``):
    the hero is landscape at column width or an inset; a square or portrait body image
    is an inset; a landscape one, a diagram or a chart takes the column; after the hero,
    about one image per 500 words at most. The class goes in essay.md's ``images:``
    front matter, which ``render`` honours as ``<img width>`` and ``publish`` as
    python-substack's image marker. ``--apply`` sets every unset image's class to the
    suggestion (a class set by hand is kept; to change one, edit the front matter).
    """
    ws = _ws(folder)
    markdown = _essay_text(ws)
    records = list(_layout.describe_images(ws.folder, markdown))
    images = [r for r in records if "image" in r]
    notes = [r["note"] for r in records if "note" in r]
    lines = [
        f"{'hero ' if r['hero'] else '     '}{r['image']}: "
        + (f"{r['pixels'][0]}x{r['pixels'][1]}" if r["pixels"] else "?")
        + f", {r['size'] or 'unset'} -> {r['suggested']} ({r['reason']})"
        for r in images
    ] + [f"note: {n}" for n in notes]
    differ = [
        r["image"]
        for r in images
        if (r["size"] or _layout.DEFAULT_SIZE) != r["suggested"]
    ]
    changed: list[str] = []
    if apply:
        sizes = {r["image"]: r["size"] or r["suggested"] for r in images}
        changed = [
            r["image"]
            for r in images
            if not r["size"] and r["suggested"] != _layout.DEFAULT_SIZE
        ]
        ws.essay.write_text(_layout.with_sizes(markdown, sizes), encoding="utf-8")
        lines.append(f"written: images: for {len(changed)} image(s); render and post again")
    return {
        "ok": True,
        "summary": f"{len(images)} image(s), {len(differ)} differ from the rules"
        + (f"; {len(changed)} set" if apply else ""),
        "images": images,
        "notes": notes,
        "differ": differ,
        "changed": changed,
        "text": "\n".join(lines),
    }


# -- render, post, approve, publish ------------------------------------------------------


def render(
    folder: str | None = None,
    *,
    raw_base: str | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Write comment.md: the essay as a GitHub comment, relative images turned into raw URLs.

    ``raw_base`` is worked out from the checkout (owner, repo, commit, folder) when
    not given; pinning the commit keeps the links alive after the branch is merged.
    The comment ends with a footer naming the seed and the research folder.
    """
    ws = _ws(folder)
    markdown = _essay_text(ws)
    state = ws.read_state()
    checkout = _gh.repo_of_checkout(ws.folder, runner=runner)
    if raw_base is None:
        if not checkout:
            raise PenultError(
                "the workspace is not in a GitHub checkout; pass --raw-base <url prefix for its files>"
            )
        raw_base = _gh.raw_url_base(checkout, ws.folder)
    version = int(state.get("draft_version", 0)) + 1
    tree_url = ""
    if checkout:
        rel = (
            ws.folder.resolve().relative_to(Path(checkout["root"]).resolve()).as_posix()
        )
        # the folder link points at the same commit as the images, which a given
        # raw_base may pin to a commit other than the local HEAD
        found = re.match(
            r"https://raw\.githubusercontent\.com/[^/]+/[^/]+/([^/]+)/", raw_base
        )
        ref = found.group(1) if found else checkout["sha"]
        tree_url = f"https://github.com/{checkout['owner']}/{checkout['repo']}/tree/{ref}/{rel}"
    footer = (
        f"*Draft v{version}, made with penult from {state.get('issue', 'the issue')}. "
        + (
            f"Research notes, images and the Substack-ready source are in [`{ws.folder.name}/`]({tree_url}). "
            if tree_url
            else ""
        )
        + "Comment with what to change; say when it is good to go and it becomes an unpublished "
        f"{state.get('platform', 'substack')} draft for you to check.*"
    )
    prefs = _prefs(data_dir, files)
    text = render_comment(
        markdown, raw_base=raw_base, footer=footer, inset_width=prefs["inset_width"]
    )
    ws.comment.write_text(text + "\n", encoding="utf-8")
    missing = [p for p in local_images(markdown) if not (ws.folder / p).is_file()]
    ws.update_state(rendered_hash=text_hash(markdown), rendered_missing=missing)
    return {
        "ok": not missing,
        "summary": f"{ws.comment.name} written (draft v{version})"
        + (f"; {len(missing)} image file(s) missing" if missing else ""),
        "path": str(ws.comment),
        "version": version,
        "missing_images": missing,
        "text": f"{ws.comment}\nimages referenced: {len(local_images(markdown))}"
        + ("\nMISSING: " + ", ".join(missing) if missing else ""),
    }


def post(
    folder: str | None = None, *, new: bool = False, runner: Callable = subprocess.run
) -> dict:
    """Post comment.md on the issue (or update the comment posted last time; ``--new`` posts another).

    Refuses while comment.md is older than essay.md, while an image the essay shows is
    missing, and while any image is not committed and pushed, since its raw URL would
    be a 404 for the reader.
    """
    ws = _ws(folder)
    if not ws.comment.is_file():
        raise PenultError(f"no {ws.comment.name}; run penult render first")
    state = ws.read_state()
    markdown = _essay_text(ws)
    if state.get("rendered_hash") != text_hash(markdown):
        raise PenultError(
            "essay.md changed since the last render; run penult render first"
        )
    images = [ws.folder / p for p in local_images(markdown)]
    missing = [str(p.relative_to(ws.folder)) for p in images if not p.is_file()]
    if missing:
        raise PenultError(
            "the essay shows images that do not exist: " + ", ".join(missing)
        )
    checkout = _gh.repo_of_checkout(ws.folder, runner=runner)
    if checkout:
        behind = _gh.unpushed(checkout, images, runner=runner)
        if behind:
            raise PenultError(
                "these images are not on GitHub yet, so the comment would show broken pictures; "
                "commit and push them first: " + ", ".join(behind)
            )
    if state.get("comment_url") and not new:
        url = _gh.edit_comment(state["comment_url"], ws.comment, runner=runner)
        what = "updated"
    else:
        url = _gh.post_comment(state["issue"], ws.comment, runner=runner)
        what = "posted"
    version = int(state.get("draft_version", 0)) + 1
    ws.update_state(
        comment_url=url,
        draft_version=version,
        posted=now(),
        posted_hash=text_hash(markdown),
    )
    ws.advance("posted")
    return {
        "ok": True,
        "summary": f"{what} draft v{version}: {url}",
        "comment_url": url,
        "version": version,
        "text": f"{what} draft v{version}\n{url}",
    }


def approve(folder: str | None = None, *, by: str = "the user", note: str = "") -> dict:
    """Record that the person is happy with the posted draft, as it stands now; this lets ``publish`` run.

    Only set it when the person said so, in their words; quote them in ``--note``. The
    approval is of this text: if essay.md changes afterwards, ``publish`` refuses until
    the person approves again.
    """
    ws = _ws(folder)
    state = ws.read_state()
    if state.get("stage") not in ("posted", "approved", "published"):
        raise PenultError(
            "nothing has been posted for review yet (penult post), so there is nothing to approve"
        )
    digest = text_hash(_essay_text(ws))
    if state.get("posted_hash") and state["posted_hash"] != digest:
        raise PenultError(
            "essay.md changed since it was posted; render and post it again so the person approves what they see"
        )
    ws.update_state(
        approved={"by": by, "at": now(), "note": note, "essay_hash": digest}
    )
    ws.advance("approved")
    return {
        "ok": True,
        "summary": f"approved by {by}",
        "text": f"approved by {by}; next: penult publish",
    }


def article_publisher(
    platform: str,
    essay: Path,
    *,
    prefs: dict,
    dry_run: bool,
    update: bool,
    runner: Callable = subprocess.run,
) -> dict:
    """The default publisher: the ``article`` package, as a command, returning its JSON record.

    Substack makes an unpublished draft (``draft-substack``); Medium is article's
    Import-a-story step (``syndicate-secondary``), which article refuses until the
    Substack post is live.
    """
    if importlib.util.find_spec("article") is None:
        raise PenultError(
            "the article package is not installed: pip install 'penult[publish]'"
        )
    common = [
        "-e",
        os.path.expanduser(prefs["article_env_file"]),
        "-s",
        os.path.expanduser(prefs["article_state_path"]),
        "--json-out",
    ]
    if platform == "substack":
        args = ["draft-substack", str(essay), *common] + (
            ["--dry-run"] if dry_run else ["--update"] if update else []
        )
    elif platform == "medium":
        if dry_run:
            raise PenultError(
                "--dry-run is a Substack check; Medium is an import step with nothing to convert"
            )
        args = ["syndicate-secondary", str(essay), *common, "--platforms", "medium"]
    else:
        raise PenultError(f"unknown platform {platform!r}; substack or medium")
    done = runner(
        [sys.executable, "-m", "article", *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )
    out = (done.stdout or "").strip()
    if done.returncode != 0:
        raise PenultError(
            f"article failed:\n{out}\n{(done.stderr or '').strip()}".strip()
        )
    try:
        record = json.loads(out)
    except ValueError:
        record = {"text": out}
    if dry_run:
        return {"draft_url": None, "record": record, "text": out}
    results = record.get("results") or []
    detail = next(
        (r.get("detail") or {} for r in results if r.get("platform") == platform), {}
    )
    return {
        "draft_url": detail.get("edit_url")
        or detail.get("url")
        or next((r.get("url") for r in results), None),
        "record": record,
        "text": out,
    }


def _platform_source(ws: Workspace, platform: str, prefs: dict, data_dir_arg) -> Path:
    """essay.md itself, or a private copy under the data root that ``article`` accepts.

    The copy drops the ``images:`` front matter (article refuses keys it does not know)
    and, for Substack, carries python-substack's image marker after each sized image and
    absolute image paths. essay.md stays the one source; the copy is derived each time.
    """
    markdown = _essay_text(ws)
    sizes = _layout.sizes_from_fields(essay_fields(markdown))
    if not sizes and "images" not in essay_fields(markdown):
        return ws.essay
    copy = _layout.with_sizes(markdown, {})
    if platform == "substack":
        copy = _layout.substack_markdown(copy, sizes, inset_width=prefs["inset_width"])
    for src in local_images(markdown):
        copy = copy.replace(f"]({src}", f"]({(ws.folder / src).resolve()}")
    target = data_dir_path(data_dir_arg) / "work" / ws.folder.name / f"{platform}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(copy, encoding="utf-8")
    return target


def publish(
    folder: str | None = None,
    *,
    platform: str | None = None,
    dry_run: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    runner: Callable = subprocess.run,
    publisher: Callable | None = None,
) -> dict:
    """Hand the approved essay to the publisher for an **unpublished** draft on the platform.

    The default publisher is the ``article`` package (Substack draft, or Medium's
    import step); the draft's editor link comes back and the person publishes by
    hand. Refuses before ``penult approve``, and after any change to essay.md since
    the approval, unless ``--dry-run`` (which converts and checks, sending nothing).
    """
    ws = _ws(folder)
    state = ws.read_state()
    prefs = _prefs(data_dir, files)
    platform = (platform or state.get("platform") or prefs["platform"]).lower()
    digest = text_hash(_essay_text(ws))
    approved = state.get("approved") or {}
    if not dry_run:
        if not approved:
            raise PenultError(
                "the person has not approved the posted draft (penult approve); use --dry-run to check the conversion only"
            )
        if approved.get("essay_hash") != digest:
            raise PenultError(
                "essay.md changed since it was approved; post it again and have the person approve the new text"
            )
    drafts = dict(state.get("draft_urls") or {})
    result = (publisher or article_publisher)(
        platform,
        _platform_source(ws, platform, prefs, data_dir),
        prefs=prefs,
        dry_run=dry_run,
        update=bool(drafts.get(platform)),
        runner=runner,
    )
    if not dry_run:
        if result.get("draft_url"):
            drafts[platform] = result["draft_url"]
        ws.update_state(draft_urls=drafts, published_to=platform, draft_made=now())
        ws.advance("published")
    link = result.get("draft_url")
    return {"ok": True, "summary": link or ("dry run ok" if dry_run else "done"), "draft_url": link, "platform": platform,
            "dry_run": dry_run, "text": (f"{platform} draft: {link}\n" if link else "") + (result.get("text") or "")}  # fmt: skip


# -- preferences -----------------------------------------------------------------------


def prefs(*, data_dir: str | None = None, files: MutableMapping | None = None) -> dict:
    """The private preferences (defaults overlaid with what the person set)."""
    current = preferences(data_dir=data_dir, files=files)
    lines = [
        f"{k}: {json.dumps(v)}"
        + ("" if DEFAULT_PREFERENCES.get(k) != v else "  (default)")
        for k, v in current.items()
    ]
    return {
        "ok": True,
        "summary": f"{len(current)} preferences",
        "preferences": current,
        "text": "\n".join(lines),
    }


def prefs_set(
    key: str,
    value: str,
    *,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Set one preference; the value must have the default's type (``2``, ``'["me","dfw"]'``, text)."""
    current = set_preference(key, value, data_dir=data_dir, files=files)
    return {
        "ok": True,
        "summary": f"{key} = {json.dumps(current[key])}",
        "preferences": current,
        "text": f"{key}: {json.dumps(current[key])}",
    }


#: The one list every surface is built from. Never write a second one.
TOOLS = [
    start, status, mark, check,
    image_search, image_generate, image_add,
    layout, render, post, approve, publish,
    prefs, prefs_set,
]  # fmt: skip
