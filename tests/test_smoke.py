"""The whole path on an invented issue, every seam on its default or a fake.

This is the definition of v1: start from an issue, write an essay, add an image,
render and post the comment, approve, publish. No network: the issue fetcher, the
command runner, the image searcher and generator are fakes.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import penult
from penult.base import PenultError

ISSUE_URL = "https://github.com/octo/essays/issues/30"

RICH_BODY = " ".join(
    ["Every transition in computing splits the experts into two camps, and the careful camp is usually right about the facts."]
    * 30
)


def fake_issue(url, body=RICH_BODY, comments=()):
    return {
        "owner": "octo", "repo": "essays", "number": 30, "url": url,
        "title": "AI and the Accretion Trap: Why Experts Underestimate Broken Technologies",
        "body": body, "author": "octo", "created": "2026-09-18T15:51:04Z", "labels": [],
        "comments": list(comments),
    }  # fmt: skip


class FakeRunner:
    """Answers the git and gh commands the verbs run, and records them."""

    def __init__(self, root: Path):
        self.root = root
        self.calls: list[list[str]] = []
        self.unpushed: set[str] = set()

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        out = ""
        if args[:3] == ["git", "-C", str(self.root)] or (args[0] == "git" and "rev-parse" in args and "--show-toplevel" in args):
            if "--show-toplevel" in args:
                out = str(self.root)
            elif "get-url" in args:
                out = "git@github.com:octo/essays.git"
            elif "--abbrev-ref" in args:
                out = "main"
            elif args[-1] == "HEAD" and "rev-parse" in args:
                out = "abc1234"
            elif "status" in args:
                out = "".join(f"?? {p}\0" for p in self.unpushed)
            elif "log" in args:
                out = ""
        elif args[:3] == ["gh", "issue", "comment"]:
            out = "https://github.com/octo/essays/issues/30#issuecomment-111\n"
        elif args[:2] == ["gh", "api"]:
            out = "{}"
        elif args[1:4] == ["-m", "article", "draft-substack"]:
            out = json.dumps({"phase": "primary", "results": [{"platform": "substack", "url": "https://octo.substack.com/p/x",
                              "detail": {"edit_url": "https://octo.substack.com/publish/post/42"}}]})
        elif args[1:3] == ["-m", "ductus"]:
            out = json.dumps({"document": {"label": "mixed-signals", "lean": 0.2, "strength": 0.4}, "segments": [
                {"lean": 1.0, "strength": 0.3, "span": {"quote": "It is important to note that this serves as a test."},
                 "signals": [{"direction": "machine", "note": "serves as: say is"}]}]})
        elif args[1:3] == ["-m", "penlike"]:
            out = json.dumps({"ok": False, "register": "essay", "discrepancies": [{"x": 1}], "text": "- colons per 100 words: 3 vs 0.5"})
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "essays"
    root.mkdir()
    monkeypatch.chdir(root)
    return root


def test_the_one_command_path(repo):
    files = {}
    runner = FakeRunner(repo)
    started = penult.start(ISSUE_URL, files=files, fetch=fake_issue, runner=runner)
    ws = Path(started["workspace"])
    assert ws == repo / "docs" / "ai-and-the-accretion-trap-why-experts-underestimate-broken"
    assert not started["thin"]["thin"]
    assert "Seed:" in (ws / "seed.md").read_text() and "[DECIDE" in (ws / "brief.md").read_text()
    assert penult.status(str(ws))["state"]["stage"] == "seeded"

    # a second start refuses to clobber, --force refetches
    with pytest.raises(PenultError):
        penult.start(ISSUE_URL, files=files, fetch=fake_issue, runner=runner)
    (ws / "brief.md").write_text("# Brief: filled in by hand\n", encoding="utf-8")
    penult.start(ISSUE_URL, files=files, fetch=fake_issue, runner=runner, force=True)
    assert (ws / "brief.md").read_text() == "# Brief: filled in by hand\n"  # --force keeps the brief

    penult.mark(str(ws), stage="researched")
    (ws / "essay.md").write_text(
        '---\ntitle: The Accretion Trap\nsubtitle: On being right too early\n---\n# The Accretion Trap\n\n'
        'A paragraph.\n\n![A modem](img/modem.png "A 1995 modem, public domain")\n\nAnother.\n',
        encoding="utf-8",
    )
    penult.mark(str(ws), stage="drafted")

    # images: a fake searcher, a fake generator within budget, then past it
    hits = penult.image_search(
        "modem", folder=str(ws), searcher=lambda q, n=8, **k: [{"url": "https://x/m.jpg", "title": "Modem", "license": "cc0", "source": "test"}]
    )["hits"]
    assert hits[0]["license"] == "cc0"
    src = repo / "modem-src.png"
    src.write_bytes(b"PNG")
    added = penult.image_add(str(src), name="modem.png", credit="A 1995 modem, public domain", folder=str(ws))
    assert (ws / "img" / "modem.png").read_bytes() == b"PNG" and added["file"] == "img/modem.png"

    def generator(prompt, *, path, **_):
        Path(path).write_bytes(b"GEN")
        return path

    first = penult.image_generate("a woodcut", name="one", folder=str(ws), files=files, generator=generator)
    second = penult.image_generate("another", name="two", folder=str(ws), files=files, generator=generator)
    third = penult.image_generate("a third", name="three", folder=str(ws), files=files, generator=generator)
    assert first["generated"] and second["generated"] and not third["generated"]
    assert "budget" in third["reason"] and not (ws / "img" / "three.png").exists()
    forced = penult.image_generate("a third", name="three", folder=str(ws), files=files, generator=generator, force=True)
    assert forced["generated"]

    # a request the provider rejects (4xx) is recorded but never counts as spent
    class Rejected(Exception):
        status_code = 400

    def refusing(prompt, *, path, **_):
        raise Rejected("Error code: 400 - unknown parameter")

    with pytest.raises(Rejected):
        penult.image_generate("rejected", name="four", folder=str(ws), files=files, generator=refusing, force=True)
    kinds = [i["kind"] for i in json.loads((ws / "penult.json").read_text())["images"]]
    assert kinds.count("generation-error") == 1 and "generated-failed" not in kinds
    ledger = (ws / "images.md").read_text()
    assert ledger.count("| generated |") == 3 and "| prompt |" in ledger and "| candidate |" in ledger

    # render: relative images become raw URLs, caption becomes a line
    rendered = penult.render(str(ws), runner=runner)
    comment = (ws / "comment.md").read_text()
    assert rendered["ok"] and "https://raw.githubusercontent.com/octo/essays/abc1234/docs/" in comment
    assert '<p align="center"><sub>A 1995 modem, public domain</sub></p>' in comment
    assert comment.startswith("# The Accretion Trap\n\n*On being right too early*")
    assert "Draft v1" in comment

    # post refuses while the image is not pushed, then posts, then updates
    runner.unpushed = {"docs/ai-and-the-accretion-trap-why-experts-underestimate-broken/img/modem.png"}
    with pytest.raises(PenultError, match="commit and push"):
        penult.post(str(ws), runner=runner)
    runner.unpushed = set()
    with pytest.raises(PenultError):
        penult.approve(str(ws))  # nothing posted yet
    posted = penult.post(str(ws), runner=runner)
    assert posted["comment_url"].endswith("#issuecomment-111") and posted["version"] == 1
    again = penult.post(str(ws), runner=runner)
    assert again["version"] == 2 and runner.calls[-1][:2] == ["gh", "api"]

    # an edit after the render is caught before posting, and before approving
    essay = ws / "essay.md"
    essay.write_text(essay.read_text() + "\nA late edit.\n", encoding="utf-8")
    with pytest.raises(PenultError, match="render first"):
        penult.post(str(ws), runner=runner)
    with pytest.raises(PenultError, match="post it again"):
        penult.approve(str(ws))
    penult.render(str(ws), runner=runner)
    penult.post(str(ws), runner=runner)

    # check runs ductus and penlike through python -m, writes under the data root, quotes the flagged text
    checked = penult.check(str(ws), files=files, data_dir=str(repo.parent / "data"), runner=runner)
    assert "serves as a test" in checked["text"] and "colons per 100 words" in checked["text"]
    assert Path(checked["path"]).is_relative_to(repo.parent / "data") and not (ws / "check.md").exists()
    committed = (ws / "penult.json").read_text() + (ws / "brief.md").read_text()
    assert "data" + "/" not in committed.replace(str(repo), "") and str(repo.parent / "data") not in committed
    assert '"me"' not in (ws / "brief.md").read_text()  # the brief never names the private voice models

    # publish is gated on approval
    with pytest.raises(PenultError, match="approve"):
        penult.publish(str(ws), files=files, runner=runner)
    penult.approve(str(ws), by="octo", note="good to go")
    essay.write_text(essay.read_text() + "\nAnother edit.\n", encoding="utf-8")
    with pytest.raises(PenultError, match="approved"):
        penult.publish(str(ws), files=files, runner=runner)  # the approval was of the earlier text
    penult.render(str(ws), runner=runner); penult.post(str(ws), runner=runner); penult.approve(str(ws), by="octo")
    published = penult.publish(str(ws), files=files, runner=runner)
    assert published["draft_url"] == "https://octo.substack.com/publish/post/42"
    assert penult.status(str(ws))["state"]["stage"] == "published"
    assert "--json-out" in runner.calls[-1] and "--dry-run" not in runner.calls[-1] and "--update" not in runner.calls[-1]
    penult.publish(str(ws), files=files, runner=runner)
    assert "--update" in runner.calls[-1]  # a second run updates the same draft


def test_a_thin_seed_is_reported_and_the_brief_says_to_ask(repo):
    runner = FakeRunner(repo)
    started = penult.start(ISSUE_URL, files={}, fetch=lambda u: fake_issue(u, body="Agents read specs"), runner=runner)
    assert started["thin"]["thin"] and started["thin"]["reasons"]
    assert "THIN: ask the user" in Path(started["workspace"], "brief.md").read_text()


def test_start_needs_the_right_checkout_or_an_explicit_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def other_repo(args, **kwargs):
        out = {"--show-toplevel": str(tmp_path), "get-url": "git@github.com:someone/else.git", "--abbrev-ref": "main"}
        found = next((v for k, v in out.items() if k in args), "")
        return subprocess.CompletedProcess(args, 0, stdout=found, stderr="")

    with pytest.raises(PenultError, match="--into"):
        penult.start(ISSUE_URL, files={}, fetch=fake_issue, runner=other_repo)
    started = penult.start(ISSUE_URL, into=str(tmp_path / "here"), files={}, fetch=fake_issue, runner=other_repo)
    assert Path(started["workspace"]) == (tmp_path / "here").resolve()


def test_preferences_have_defaults_and_keep_only_changes():
    files = {}
    assert penult.prefs(files=files)["preferences"]["max_generated_images"] == 2
    penult.prefs_set("max_generated_images", "1", files=files)
    penult.prefs_set("voice_models", '["me", "dan-luu"]', files=files)
    saved = json.loads(files["config/preferences.json"])
    assert saved == {"max_generated_images": 1, "voice_models": ["me", "dan-luu"]}
    with pytest.raises(PenultError, match="unknown preference"):
        penult.prefs_set("colour", "blue", files=files)
    with pytest.raises(PenultError, match="takes a list"):
        penult.prefs_set("voice_models", "me", files=files)
    with pytest.raises(PenultError, match="takes a int"):
        penult.prefs_set("max_generated_images", "two", files=files)


def test_importing_the_package_loads_no_surface_library():
    import subprocess as sp
    import sys

    code = "import sys, penult; print([m for m in ('cw', 'illustration', 'aix', 'ductus', 'penlike') if m in sys.modules])"
    done = sp.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.stdout.strip() == "[]", done.stderr


def test_the_command_line_runs(tmp_path):
    import os
    import subprocess as sp
    import sys

    env = {**os.environ, "PENULT_DATA_DIR": str(tmp_path / "data")}
    done = sp.run([sys.executable, "-m", "penult", "prefs"], capture_output=True, text=True, env=env)
    assert done.returncode == 0 and "platform" in done.stdout
    done = sp.run([sys.executable, "-m", "penult", "status", str(tmp_path)], capture_output=True, text=True, env=env)
    assert done.returncode != 0 and "penult start" in done.stderr
