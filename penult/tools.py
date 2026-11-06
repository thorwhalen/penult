"""The verbs: plain functions, JSON-ready in and out, the one list every surface is built from.

An agent drives an essay from a seed to a reviewed draft with these, in this order::

    start      fetch the issue, make the workspace, say whether the seed is thin
    status     where the workspace stands and what comes next
    check      ductus and penlike over the essay: what still reads machine-made or off-voice
    image-search / image-generate / image-add   images, within the budget, all credited
    render     the essay as an issue comment, images as raw URLs
    post       post (or update) that comment on the issue
    approve    record that the person is happy with the posted draft
    publish    hand the approved essay to ``article`` for an unpublished platform draft
    prefs / prefs-set   the private preferences

The thinking (research, drafting, the style passes) is the agent's and is laid out
in the ``penult`` skill; these verbs hold the state, the files, the budget and the
hand-offs so that no step is improvised twice. Nothing here prints or exits: the
command line and any other surface wrap :data:`TOOLS`.
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import re
import shutil
import subprocess
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Callable

from penult import github as _gh
from penult import images as _images
from penult.base import STAGES, PenultError
from penult.render import local_images, render_comment
from penult.store import DEFAULT_PREFERENCES, preferences, set_preference
from penult.workspace import Workspace, brief_markdown, is_thin, now, seed_markdown, slug_of

__all__ = ["HIDDEN_PARAMETERS", "TOOLS", "without"]

#: Parameters a surface built from these signatures leaves out: the in-memory store and
#: the injected callables are for Python callers and tests.
HIDDEN_PARAMETERS = ("files", "fetch", "runner", "searcher", "generator")


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


# -- start and status ------------------------------------------------------------------


def start(
    issue_url: str,
    *,
    into: str | None = None,
    force: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    fetch: Callable[..., dict] | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Fetch the issue and make the workspace: seed, brief, state. Says whether the seed is thin.

    The workspace goes ``into`` the folder given, else to the ``workspace`` preference
    (``docs/<slug>`` by default) inside the checkout of the issue's own repository
    that holds the current directory. A thin seed (few words, no thesis) is reported
    so the agent asks the user before researching.
    """
    issue = (fetch or functools.partial(_gh.fetch_issue, runner=runner))(issue_url)
    prefs = _prefs(data_dir, files)
    slug = slug_of(issue["title"])
    if into:
        folder = Path(into).expanduser()
    else:
        checkout = _gh.repo_of_checkout(Path(os.getcwd()), runner=runner)
        same_repo = checkout and (checkout["owner"], checkout["repo"]) == (issue["owner"], issue["repo"])
        if not same_repo:
            raise PenultError(
                f"the current directory is not a checkout of {issue['owner']}/{issue['repo']}; "
                f"run from one, or say where the workspace goes with --into <folder>"
            )
        folder = Path(checkout["root"]) / prefs["workspace"].format(slug=slug)
    ws = Workspace(folder)
    if ws.exists() and not force:
        raise PenultError(f"{ws.folder} already holds a workspace; use --force to refetch the seed into it")
    thin = is_thin(issue)
    ws.folder.mkdir(parents=True, exist_ok=True)
    ws.seed.write_text(seed_markdown(issue), encoding="utf-8")
    if not ws.brief.is_file() or force:
        ws.brief.write_text(brief_markdown(issue, prefs, thin), encoding="utf-8")
    (ws.research).mkdir(exist_ok=True)
    (ws.img).mkdir(exist_ok=True)
    state = ws.read_state()
    state.update(
        issue=issue["url"], issue_title=issue["title"], repo=f"{issue['owner']}/{issue['repo']}",
        number=issue["number"], slug=slug, stage="seeded", thin=thin["thin"], seed_words=thin["words"],
        platform=prefs["platform"], created=state.get("created") or now(), updated=now(),
    )  # fmt: skip
    state.setdefault("images", [])
    ws.write_state(state)
    verdict = "THIN: ask the user before researching" if thin["thin"] else "rich enough: decide the brief and go on"
    return {
        "ok": True,
        "summary": f"workspace {ws.folder} ({verdict})",
        "workspace": str(ws.folder),
        "slug": slug,
        "thin": thin,
        "files": {"seed": str(ws.seed), "brief": str(ws.brief), "state": str(ws.state_file)},
        "next": "fill brief.md (ask the user if thin), then research into research/, then write essay.md",
        "text": f"{ws.folder}\nseed: {thin['words']} words; {verdict}\n"
        + ("\n".join(f"  - {r}" for r in thin["reasons"]) + "\n" if thin["reasons"] else "")
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
    if state.get("draft_url"):
        lines.append(f"platform draft: {state['draft_url']}")
    lines.append(f"next: {nxt}")
    return {"ok": True, "summary": f"{stage}", "state": state, "files": present, "next": nxt, "text": "\n".join(lines)}


def mark(folder: str | None = None, *, stage: str) -> dict:
    """Record that the workspace reached ``stage`` (researched, drafted, styled, illustrated)."""
    ws = _ws(folder)
    if stage not in STAGES:
        raise PenultError(f"unknown stage {stage!r}; one of: {', '.join(STAGES)}")
    if stage in ("posted", "approved", "published"):
        raise PenultError(f"{stage!r} is set by penult post / approve / publish, not by hand")
    state = ws.advance(stage)
    return {"ok": True, "summary": f"stage {state['stage']}", "stage": state["stage"]}


# -- checks ----------------------------------------------------------------------------


def _tool_json(args: list[str], *, runner: Callable) -> dict | None:
    if shutil.which(args[0]) is None:
        return None
    done = runner(args, capture_output=True, text=True)
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
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Read the essay with ductus and penlike, and write what they found to check.md.

    ductus marks the segments that read machine-made (lean toward +1, with the
    evidence strength); penlike measures the draft against each voice model in
    ``like`` (the ``voice_models`` preference by default). The agent's own reading
    comes on top of this; neither tool sees bland prose that carries no tell.
    """
    ws = _ws(folder)
    if not ws.essay.is_file():
        raise PenultError(f"no {ws.essay.name} to check yet")
    prefs = _prefs(data_dir, files)
    like = like or prefs["voice_models"]
    style = style or prefs["voice_register"]
    report: dict[str, Any] = {"when": now(), "ductus": None, "penlike": {}}
    lines = [f"# Check of {ws.essay.name}, {now()[:16]}", ""]

    gauge = _tool_json(["ductus", "gauge", str(ws.essay), "--format", "json"], runner=runner)
    if gauge is None:
        lines += ["ductus: not installed (pip install ductus); the agent reads for machine-sounding passages alone.", ""]
    elif "error" in gauge:
        lines += [f"ductus: failed: {gauge['error']}", ""]
    else:
        doc = gauge.get("document", {})
        segments = gauge.get("segments", [])
        flagged = sorted(
            (s for s in segments if (s.get("lean") or 0) > 0 and (s.get("strength") or 0) > 0),
            key=lambda s: -(s.get("lean", 0) * s.get("strength", 0)),
        )
        report["ductus"] = {"label": doc.get("label"), "lean": doc.get("lean"), "strength": doc.get("strength"), "flagged": len(flagged)}
        lines += [
            f"## ductus: {doc.get('label')} (lean {doc.get('lean')}, strength {doc.get('strength')}); {len(flagged)} segment(s) lean machine",
            "",
        ]
        for seg in flagged[:25]:
            text = (seg.get("text") or "").strip().replace("\n", " ")
            reasons = "; ".join(sig.get("note", "") for sig in seg.get("signals", [])[:2] if sig.get("direction") == "machine")
            lines.append(f"- lean {seg.get('lean'):+.2f} / strength {seg.get('strength'):.2f}: \"{text[:160]}\"" + (f" ({reasons})" if reasons else ""))
        lines.append("")

    for model in like:
        result = _tool_json(["penlike", "check", str(ws.essay), "--like", model, "--style", style, "--json"], runner=runner)
        if result is None:
            lines += [f"penlike: not installed (pip install penlike); voice not measured.", ""]
            break
        if "error" in result and "discrepancies" not in result:
            lines += [f"## penlike {model}: failed: {result['error']}", ""]
            continue
        discrepancies = result.get("discrepancies", [])
        report["penlike"][model] = {"register": result.get("register"), "discrepancies": len(discrepancies)}
        lines += [f"## penlike against `{model}` ({result.get('register')}): {len(discrepancies)} discrepancies", ""]
        lines += [f"- {line}" for line in (result.get("text") or "").splitlines() if line.strip()][:30]
        lines.append("")

    ws.check_report.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    ws.update_state(last_check=report)
    return {"ok": True, "summary": f"check written to {ws.check_report.name}", "report": report, "path": str(ws.check_report), "text": "\n".join(lines)}


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
    lines = [f"{i}. {_images.credit_line(h)}\n   {h['url']}" + (f"\n   page: {h['page']}" if h.get("page") else "") for i, h in enumerate(hits, 1)]
    return {"ok": True, "summary": f"{len(hits)} candidate(s) for {query!r}", "hits": hits, "text": "\n".join(lines) or "no candidates"}


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
        ws, prompt, name=name, max_generated=int(prefs["max_generated_images"]), force=force, generator=generator
    )
    text = f"generated {result['file']}" if result["generated"] else f"not generated: {result['reason']}"
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
    path = _images.add_image(ws, source, name=name, credit=credit, license=license, prompt=prompt)
    rel = f"img/{path.name}"
    return {"ok": True, "summary": f"added {rel}", "file": rel, "markdown": f'![ALT]({rel} "{credit}")', "text": f"{rel}\n![ALT]({rel} \"{credit}\")"}


# -- render, post, approve, publish ------------------------------------------------------


def render(folder: str | None = None, *, raw_base: str | None = None, runner: Callable = subprocess.run) -> dict:
    """Write comment.md: the essay as a GitHub comment, relative images turned into raw URLs.

    ``raw_base`` is worked out from the checkout (owner, repo, branch, folder) when not
    given. The comment ends with a footer naming the seed and the research folder.
    """
    ws = _ws(folder)
    if not ws.essay.is_file():
        raise PenultError(f"no {ws.essay.name} to render yet")
    state = ws.read_state()
    checkout = _gh.repo_of_checkout(ws.folder, runner=runner)
    if raw_base is None:
        if not checkout:
            raise PenultError("the workspace is not in a GitHub checkout; pass --raw-base <url prefix for its files>")
        raw_base = _gh.raw_url_base(checkout, ws.folder)
    markdown = ws.essay.read_text(encoding="utf-8")
    version = int(state.get("draft_version", 0)) + 1
    folder_url = raw_base.replace("raw.githubusercontent.com", "github.com").rsplit("/", 2)
    tree_url = f"https://github.com/{checkout['owner']}/{checkout['repo']}/tree/{checkout['branch']}/{ws.folder.relative_to(checkout['root']).as_posix()}" if checkout else ""
    footer = (
        f"*Draft v{version}, made with penult from {state.get('issue', 'the issue')}. "
        + (f"Research notes, images and the Substack-ready source are in [`{ws.folder.name}/`]({tree_url}). " if tree_url else "")
        + "Comment with what to change; say when it is good to go and it becomes an unpublished "
        f"{state.get('platform', 'substack')} draft for you to check.*"
    )
    del folder_url
    text = render_comment(markdown, raw_base=raw_base, footer=footer)
    ws.comment.write_text(text + "\n", encoding="utf-8")
    missing = [p for p in local_images(markdown) if not (ws.folder / p).is_file()]
    return {
        "ok": not missing,
        "summary": f"{ws.comment.name} written (draft v{version})" + (f"; {len(missing)} image file(s) missing" if missing else ""),
        "path": str(ws.comment),
        "version": version,
        "missing_images": missing,
        "text": f"{ws.comment}\nimages referenced: {len(local_images(markdown))}" + ("\nMISSING: " + ", ".join(missing) if missing else ""),
    }


def post(folder: str | None = None, *, new: bool = False, runner: Callable = subprocess.run) -> dict:
    """Post comment.md on the issue (or update the comment posted last time; ``--new`` posts another).

    Refuses while an image the comment shows is not committed and pushed, since its
    raw URL would be a 404 for the reader.
    """
    ws = _ws(folder)
    if not ws.comment.is_file():
        raise PenultError(f"no {ws.comment.name}; run penult render first")
    state = ws.read_state()
    checkout = _gh.repo_of_checkout(ws.folder, runner=runner)
    if checkout:
        images = [ws.folder / p for p in local_images(ws.essay.read_text(encoding="utf-8"))]
        behind = _gh.unpushed(checkout, [p for p in images if p.is_file()], runner=runner)
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
    ws.update_state(comment_url=url, draft_version=version, posted=now())
    ws.advance("posted")
    return {"ok": True, "summary": f"{what} draft v{version}: {url}", "comment_url": url, "version": version, "text": f"{what} draft v{version}\n{url}"}


def approve(folder: str | None = None, *, by: str = "the user", note: str = "") -> dict:
    """Record that the person is happy with the posted draft; this is what lets ``publish`` run.

    Only set it when the person said so, in their words; quote them in ``--note``.
    """
    ws = _ws(folder)
    state = ws.read_state()
    if state.get("stage") not in ("posted", "approved", "published"):
        raise PenultError("nothing has been posted for review yet (penult post), so there is nothing to approve")
    ws.update_state(approved={"by": by, "at": now(), "note": note})
    ws.advance("approved")
    return {"ok": True, "summary": f"approved by {by}", "text": f"approved by {by}; next: penult publish"}


def publish(
    folder: str | None = None,
    *,
    platform: str | None = None,
    dry_run: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
    runner: Callable = subprocess.run,
) -> dict:
    """Hand the approved essay to ``article`` for an **unpublished** draft on the platform.

    Substack: ``article draft-substack essay.md`` with the credentials file and state
    path from the preferences; the draft's editor link comes back and the person
    publishes by hand. Medium: article's Import-a-story step, after the Substack
    post is live. Refuses before ``penult approve`` unless ``--dry-run``.
    """
    ws = _ws(folder)
    state = ws.read_state()
    prefs = _prefs(data_dir, files)
    platform = (platform or state.get("platform") or prefs["platform"]).lower()
    if not dry_run and not state.get("approved"):
        raise PenultError("the person has not approved the posted draft (penult approve); use --dry-run to check the conversion only")
    if shutil.which("article") is None:
        raise PenultError("the article package is not installed: pip install 'article[substack]'")
    if platform == "substack":
        args = ["article", "draft-substack", str(ws.essay), "-e", os.path.expanduser(prefs["article_env_file"]),
                "-s", os.path.expanduser(prefs["article_state_path"])]  # fmt: skip
        if dry_run:
            args.append("--dry-run")
        elif state.get("draft_url"):
            args.append("--update")
    elif platform == "medium":
        args = ["article", "syndicate-secondary", str(ws.essay), "-e", os.path.expanduser(prefs["article_env_file"]),
                "-s", os.path.expanduser(prefs["article_state_path"]), "--platforms", "medium"]  # fmt: skip
    else:
        raise PenultError(f"unknown platform {platform!r}; substack or medium")
    done = runner(args, capture_output=True, text=True)
    out = (done.stdout or "") + (("\n" + done.stderr) if done.stderr else "")
    if done.returncode != 0:
        raise PenultError(f"article failed:\n{out.strip()}")
    link = re.search(r"https?://\S+", out[out.find("Edit the draft:"):]) if "Edit the draft:" in out else None
    if not dry_run:
        ws.update_state(draft_url=link.group(0) if link else None, published_to=platform, draft_made=now())
        ws.advance("published")
    return {"ok": True, "summary": (link.group(0) if link else out.strip().splitlines()[-1] if out.strip() else "done"),
            "draft_url": link.group(0) if link else None, "platform": platform, "dry_run": dry_run, "text": out.strip()}  # fmt: skip


# -- preferences -----------------------------------------------------------------------


def prefs(*, data_dir: str | None = None, files: MutableMapping | None = None) -> dict:
    """The private preferences (defaults overlaid with what the person set)."""
    current = preferences(data_dir=data_dir, files=files)
    lines = [f"{k}: {json.dumps(v)}" + ("" if DEFAULT_PREFERENCES.get(k) != v else "  (default)") for k, v in current.items()]
    return {"ok": True, "summary": f"{len(current)} preferences", "preferences": current, "text": "\n".join(lines)}


def prefs_set(key: str, value: str, *, data_dir: str | None = None, files: MutableMapping | None = None) -> dict:
    """Set one preference (JSON values parse: ``2``, ``'["me","dfw"]'``; else text)."""
    current = set_preference(key, value, data_dir=data_dir, files=files)
    return {"ok": True, "summary": f"{key} = {json.dumps(current[key])}", "preferences": current, "text": f"{key}: {json.dumps(current[key])}"}


#: The one list every surface is built from. Never write a second one.
TOOLS = [
    start, status, mark, check,
    image_search, image_generate, image_add,
    render, post, approve, publish,
    prefs, prefs_set,
]  # fmt: skip
