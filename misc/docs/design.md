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
| 2 | how issues are read and comments posted | the `gh` command, `fetch=` / `runner=` | `hubcap` (PyGithub wrapper in the fleet), the REST API |
| 3 | image search | `illustration.search`, `searcher=` | any callable returning hits with url / licence / attribution |
| 4 | image generation | `aix.image.generate_image`, `generator=` | `falaw` (used for the Agile, Reformed woodcuts), any `(prompt, path=) -> path` |
| 5 | publishing | `article draft-substack` (substack), `article syndicate-secondary` (medium) | article's other adapters (dev.to, hashnode) when they go live |

Surface for v1: the shipped `penult` skill and the CLI (`cw.dispatch` over `TOOLS`). MCP would need no core change (verbs are JSON in/out); HTTP would need per-request state (the workspace is already a path argument, so none is global). Not built.

NOT seams, written directly: the thin-seed rule (word count and a sentence), the workspace layout, the GitHub-comment template, the check report format, the stage names.

## Concerns kept apart

- **Preferences** (user-facing seam): one JSON file with defaults in code; `prefs` / `prefs-set`. The author-choice guide is *not* here: which penlike model fits which situation is penlike's concern (`penlike guide`), and penult only names the base voice.
- **The thinking** (research, drafting, voice passes) is the agent's and lives in the skill, which points at the skills that own each step. The package holds no prompts.
- **Credentials** are never read by penult; `publish` passes the path of the `article` credentials file.

## The next changes already known

- A second seed type (a Markdown file, a Discussion) would be a second `fetch` implementation behind seam 2; `start` already takes the fetched dict.
- Image display width on Substack is `article`'s open issue (#11); nothing in penult changes for it.
- A Medium path that does not wait for the Substack post to be live would be a flag on `publish`, inside seam 5.
