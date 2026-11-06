"""GitHub, through the ``gh`` and ``git`` commands: read an issue, post or edit a comment, find raw URLs.

Every function takes a ``runner`` (the shape of :func:`subprocess.run`) so tests
run without a network and another transport can be dropped in. The default needs
an authenticated ``gh``.

>>> parse_issue_url("https://github.com/octo/essays/issues/30")
('octo', 'essays', 30)
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from penult.base import PenultError

__all__ = [
    "edit_comment",
    "fetch_issue",
    "parse_issue_url",
    "post_comment",
    "raw_url_base",
    "repo_of_checkout",
    "unpushed",
]

Runner = Callable[..., Any]

_ISSUE_URL = re.compile(r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/issues/(\d+)(?:[/#?].*)?$")
_REMOTE = re.compile(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$")
_TIMEOUT = 600


def parse_issue_url(url: str) -> tuple[str, str, int]:
    """``(owner, repo, number)`` from an issue URL, or an error that shows the shape."""
    found = _ISSUE_URL.match(url.strip())
    if not found:
        raise PenultError(
            f"not a GitHub issue URL: {url!r}; expected https://github.com/<owner>/<repo>/issues/<n>"
        )
    owner, repo, number = found.groups()
    return owner, repo, int(number)


def _run(runner: Runner, args: list[str], *, what: str, **kwargs: Any) -> str:
    try:
        done = runner(args, capture_output=True, text=True, timeout=_TIMEOUT, **kwargs)
    except FileNotFoundError as error:
        raise PenultError(f"{args[0]!r} is not installed; it is needed to {what}") from error
    if done.returncode != 0:
        detail = (done.stderr or done.stdout or "").strip()
        raise PenultError(f"could not {what}: {detail or 'command failed'}")
    return done.stdout or ""


def fetch_issue(url: str, *, runner: Runner = subprocess.run) -> dict[str, Any]:
    """The issue's title, body, labels and comments, as one JSON-ready dict."""
    owner, repo, number = parse_issue_url(url)
    out = _run(
        runner,
        ["gh", "issue", "view", str(number), "-R", f"{owner}/{repo}", "--json",
         "title,body,labels,comments,url,author,createdAt"],
        what=f"read issue {owner}/{repo}#{number}",
    )  # fmt: skip
    raw = json.loads(out)
    return {
        "kind": "github-issue",
        "owner": owner,
        "repo": repo,
        "number": number,
        "url": raw.get("url") or url,
        "title": raw.get("title", ""),
        "body": raw.get("body") or "",
        "author": (raw.get("author") or {}).get("login", ""),
        "created": raw.get("createdAt", ""),
        "labels": [label.get("name", "") for label in raw.get("labels") or []],
        "comments": [
            {
                "author": (c.get("author") or {}).get("login", ""),
                "created": c.get("createdAt", ""),
                "body": c.get("body") or "",
                "url": c.get("url", ""),
            }
            for c in raw.get("comments") or []
        ],
    }


def post_comment(url: str, body_file: Path, *, runner: Runner = subprocess.run) -> str:
    """Post a file's content as a comment on the issue; returns the comment's URL."""
    owner, repo, number = parse_issue_url(url)
    out = _run(
        runner,
        ["gh", "issue", "comment", str(number), "-R", f"{owner}/{repo}", "--body-file", str(body_file)],
        what=f"comment on {owner}/{repo}#{number}",
    )  # fmt: skip
    return out.strip().splitlines()[-1] if out.strip() else ""


def edit_comment(comment_url: str, body_file: Path, *, runner: Runner = subprocess.run) -> str:
    """Replace an existing comment's body (``comment_url`` ends in ``#issuecomment-<id>``)."""
    found = re.search(r"github\.com/([^/]+)/([^/]+)/issues/\d+#issuecomment-(\d+)", comment_url)
    if not found:
        raise PenultError(f"not an issue-comment URL: {comment_url!r}")
    owner, repo, comment_id = found.groups()
    payload = json.dumps({"body": Path(body_file).read_text(encoding="utf-8")})
    _run(
        runner,
        ["gh", "api", "-X", "PATCH", f"repos/{owner}/{repo}/issues/comments/{comment_id}", "--input", "-"],
        what=f"edit comment {comment_id}",
        input=payload,
    )  # fmt: skip
    return comment_url


def repo_of_checkout(path: Path, *, runner: Runner = subprocess.run) -> dict[str, Any] | None:
    """The checkout holding ``path``: its root, GitHub owner/repo, branch and commit, or ``None``."""
    try:
        git = ["git", "-C", str(path)]
        root = _run(runner, [*git, "rev-parse", "--show-toplevel"], what="find the repo").strip()
        git = ["git", "-C", root]
        remote = _run(runner, [*git, "remote", "get-url", "origin"], what="read the remote").strip()
        branch = _run(runner, [*git, "rev-parse", "--abbrev-ref", "HEAD"], what="read the branch").strip()
        sha = _run(runner, [*git, "rev-parse", "HEAD"], what="read the commit").strip()
    except PenultError:
        return None
    found = _REMOTE.search(remote) if "github" in remote else None
    if not found:
        return None
    owner, repo = found.groups()
    return {"root": root, "owner": owner, "repo": repo, "branch": branch, "sha": sha or branch}


def raw_url_base(checkout: dict[str, Any], folder: Path) -> str:
    """The ``raw.githubusercontent.com`` prefix for files in ``folder`` at the checkout's commit.

    The commit, not the branch, so the links keep working after the branch is
    merged and deleted.

    >>> raw_url_base({"root": "/r", "owner": "o", "repo": "e", "branch": "main", "sha": "abc123"}, Path("/r/docs/an essay"))
    'https://raw.githubusercontent.com/o/e/abc123/docs/an%20essay/'
    """
    rel = Path(folder).resolve().relative_to(Path(checkout["root"]).resolve()).as_posix()
    rel = quote(rel) + "/" if rel not in ("", ".") else ""
    ref = checkout.get("sha") or checkout["branch"]
    return f"https://raw.githubusercontent.com/{checkout['owner']}/{checkout['repo']}/{ref}/{rel}"


def _status_paths(porcelain_z: str) -> set[str]:
    """Paths in ``git status --porcelain -z`` output (a rename lists its old path too).

    >>> sorted(_status_paths("?? a.png\\0R  new.png\\0old.png\\0"))
    ['a.png', 'new.png', 'old.png']
    """
    found: set[str] = set()
    entries = [e for e in porcelain_z.split("\0") if e]
    i = 0
    while i < len(entries):
        entry = entries[i]
        found.add(entry[3:] if len(entry) > 3 else entry)
        if entry[:1] in ("R", "C") and i + 1 < len(entries):
            found.add(entries[i + 1])
            i += 1
        i += 1
    return found


def unpushed(checkout: dict[str, Any], paths: list[Path], *, runner: Runner = subprocess.run) -> list[str]:
    """Which of ``paths`` are not yet committed and pushed to the branch's upstream.

    A raw URL only works for a file that is on GitHub, so ``post`` refuses while any
    image it references is in this list. Paths are compared in git's own form
    (forward slashes, unescaped thanks to ``-z``).
    """
    root = Path(checkout["root"]).resolve()
    names = [Path(p).resolve().relative_to(root).as_posix() for p in paths]
    if not names:
        return []
    git = ["git", "-C", str(root)]
    dirty = _run(runner, [*git, "status", "--porcelain", "-z", "--", *names], what="check the tree")
    missing = _status_paths(dirty)
    try:
        ahead = _run(
            runner,
            [*git, "log", "--name-only", "-z", "--pretty=format:", "@{upstream}..HEAD", "--", *names],
            what="compare with the upstream",
        )
        missing |= {p.strip() for p in re.split(r"[\0\n]", ahead) if p.strip()}
    except PenultError:
        missing |= set(names)  # no upstream: nothing of this branch is on GitHub
    return sorted(n for n in names if n in missing)
