# Design

*2026-11-06. Decided before the first commit (the `architecture-first` procedure). What sits inside each boundary is the simplest thing that works; later iterations add at these boundaries.*

## The decision: a new package, not an extension of `article`

`article` turns a Markdown file into an unpublished Substack draft and syndicates with canonical URLs. It is a publishing adapter and should stay one: its PyPI release must not depend on an LLM, an agent host, an image API or a style model. The path from an idea to that Markdown file is a different concern (a workbench for an agent: workspace, state, budgets, review loop) that *depends on* `article`, `penlike`, `ductus`, `illustration` and `aix`. So: `penult` (the penultimate step), with `article` as its publishing seam.

## v1 is done when

```
penult start <issue url> && penult status <ws>   # workspace with seed and brief, thin-seed verdict
# ... the agent researches, drafts, styles, adds images ...
penult render <ws> && penult post <ws>           # the draft is a comment on the issue, images inline
penult approve <ws> && penult publish <ws>       # an unpublished Substack draft, editor link printed
```

`tests/test_smoke.py::test_the_one_command_path` is that command with fakes for every external call. It must keep passing after any seam swap.

## Seam table

| # | Seam | v1 default (no new dependency) | Replacement you can point at |
|---|---|---|---|
| 1 | where private preferences live | `dol` files under `~/.local/share/penult`, `files=` | any `MutableMapping` (tests pass a dict); the same seam as penlike's store |
| 2 | the seed, and how it is read and commented on | a GitHub issue through the `gh` command: `fetch=` returns the seed dict (`kind`, owner, repo, number, url, title, body, comments), `runner=` runs the commands | another transport is a `runner`; another seed *kind* (a Markdown file, a Discussion) is a new `fetch` and a `kind` branch inside `start` and `post`, not a caller change: the CLI argument is already `seed` |
| 3 | image search | `illustration.search`, `searcher=` | any callable returning hits with url / licence / attribution |
| 4 | image generation | `aix.image.generate_image`, `generator=` | `falaw` (used for the Agile, Reformed woodcuts), any `(prompt, path=) -> path` |
| 5 | publishing | `article_publisher`: the `article` command with `--json-out` (Substack draft; Medium import step), `publisher=` | any `(platform, essay, prefs=, dry_run=, update=) -> {draft_url}`; article's other adapters when they go live |

Surface for v1: the shipped `penult` skill and the CLI (`cw.dispatch` over `TOOLS`). MCP would need no core change (verbs are JSON in/out); HTTP would need per-request state (the workspace is already a path argument, so none is global). Not built.

NOT seams, written directly: the thin-seed rule (word count and a sentence), the workspace layout, the GitHub-comment template, the check report format, the stage names.

## Concerns kept apart

- **Preferences** (user-facing seam): one JSON file with defaults in code; `prefs` / `prefs-set`. The author-choice guide is *not* here: which penlike model fits which situation is penlike's concern (`penlike guide`), and penult only names the base voice.
- **The thinking** (research, drafting, voice passes) is the agent's and lives in the skill, which points at the skills that own each step. The package holds no prompts.
- **Credentials** are never read by penult; `publish` passes the path of the `article` credentials file.

## The next changes already known

- A second seed kind (a Markdown file, a Discussion) is a new `fetch` behind seam 2 plus a `kind` branch inside `start` (where the workspace goes) and `post` (where the review happens); the CLI argument is already `seed`, so callers do not change.
- Image display width is settled (2026-11-06, after the author found the square hero too big): `penult.figures` holds size classes and the rules from `misc/docs/research/2026-11-06-illustration-layout-for-essays.md`; the class lives in `essay.md`'s `images:` front matter; `render` emits `<img width>`, `publish` hands article a private copy with python-substack's `<!-- python-substack-image:v1 ... -->` marker after each sized image, so `article` needed no change (its issue #11 is answered by the marker). Not a seam: the classes and their pixel mappings are written directly; `inset_width` is the one preference.
- A Medium path that does not wait for the Substack post to be live would be a flag on `publish`, inside seam 5.

## Review

The adversarial review of v1 is `review-v1.md`; its blockers and majors were fixed before the merge (private check output moved under the data root, image origins kept only when URLs, Windows path form, ductus span quotes, subtitle spacing, approval and render bound to the essay's hash, `--force` keeps the brief, a `publish` extra, `python -m` instead of `which`, raw URLs pinned to the commit, `-z` git parsing, `--json-out` and per-platform draft links, a User-Agent for downloads, typed preferences, a `publisher=` seam, honest wording about the public comment). The minors it lists that are not fixed are the backlog.
