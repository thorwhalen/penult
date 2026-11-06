# penult: map for the agent working on this repository

penult takes a seed (a GitHub issue) to a publication draft posted for review, then to an unpublished platform draft through `article`. It holds state, files, budgets and hand-offs; the thinking is in the shipped `penult` skill. Design record: `misc/docs/design.md`. Research: `misc/docs/research.md`.

## Seams and surfaces

| Seam | Default | Where |
|---|---|---|
| store (private preferences) | `dol` files under the user data folder | `penult/store.py`, `files=` on every verb |
| issue transport | the `gh` command | `penult/github.py`, `fetch=` / `runner=` |
| image search | `illustration.search` | `penult/images.py`, `searcher=` |
| image generation | `aix.image.generate_image` | `penult/images.py`, `generator=` |
| publishing | `article draft-substack` / `syndicate-secondary` | `penult/tools.py:publish` |

Surfaces built: the shipped skill (primary) and the command line, both from `penult.tools.TOOLS`. Never write a second list of verbs. NOT seams, written directly: the thin-seed rule, the workspace layout, the comment template, the check report.

## Rules

1. **No private data in this repository.** Preferences, penlike models, credentials live under the user data folders. Tests use an invented issue and fakes for every external call.
2. Verbs take and return JSON-ready values, take no `*args`, hold no state between calls, and never print or exit.
3. The core imports no surface library and none of the optional packages at import time (`cw`, `illustration`, `aix`, `ductus`, `penlike` are imported where used or called as commands); `tests/test_smoke.py` checks it.
4. The skill lives in `penult/data/skills/penult/`; `.claude/skills/penult` is a relative symlink to it. A command named in the skill must be a verb.
5. penult never publishes: `publish` makes an unpublished draft and only after `approve`.
6. A merge to `main` publishes to PyPI.
