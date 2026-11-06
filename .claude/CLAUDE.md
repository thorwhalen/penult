# penult: map for the agent working on this repository

penult takes a seed (a GitHub issue) to a publication draft posted for review, then to an unpublished platform draft through `article`. It holds state, files, budgets and hand-offs; the thinking is in the shipped `penult` skill. Design record: `misc/docs/design.md`. Research: `misc/docs/research.md`.

## Seams and surfaces

| Seam | Default | Where |
|---|---|---|
| store (private preferences) | `dol` files under the user data folder | `penult/store.py`, `files=` on every verb |
| seed and transport | a GitHub issue through the `gh` command | `penult/github.py`, `fetch=` (the seed dict) / `runner=` (the commands); a second seed kind is a new `fetch` plus a `kind` branch in `start` and `post` |
| image search | `illustration.search` | `penult/images.py`, `searcher=` |
| image generation | `aix.image.generate_image` | `penult/images.py`, `generator=` |
| publishing | `article_publisher` (the `article` command, JSON out) | `penult/tools.py`, `publisher=` on `publish` |

Surfaces built: the shipped skill (primary) and the command line, both from `penult.tools.TOOLS`. Never write a second list of verbs. NOT seams, written directly: the thin-seed rule, the workspace layout, the comment template, the check report.

## Rules

1. **No private data in this repository.** Preferences, penlike models, credentials live under the user data folders. Tests use an invented issue and fakes for every external call.
2. Verbs take and return JSON-ready values, take no `*args`, hold no state between calls, and never print or exit.
3. The core imports no surface library and none of the optional packages at import time (`cw`, `illustration`, `aix`, `ductus`, `penlike` are imported where used or called as commands); `tests/test_smoke.py` checks it.
4. The skill lives in `penult/data/skills/penult/`; `.claude/skills/penult` is a relative symlink to it. A command named in the skill must be a verb.
5. penult never publishes to a platform: `publish` makes an unpublished draft, only after `approve`, and only of the text that was approved (hash-checked). The check report holds private style figures and is written under the data root, never into the workspace.
6. A merge to `main` publishes to PyPI.
