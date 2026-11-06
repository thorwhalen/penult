# Research: what existed before penult

*2026-11-06 · scope: the fleet's own packages, skills and reports for the idea-to-draft path; a free name · requested for: whether to extend `article` or build a new package.*

## Summary and recommendation

Everything the path needs exists as separate components; nothing orchestrates them. `article` publishes Markdown to Substack and syndicates [1]; `penlike` models voices [2]; `ductus` finds machine-sounding passages [3]; `illustration` finds credited images [4]; `aix` generates images [5]; the `do-research`, `deslop` and `acquaint-write` skills own research and prose. The precedent essay (Agile, Reformed, essays#31) was produced by hand-composing these over three weeks, and the briefing of that process is the specification for the orchestration [6]. Recommendation: a new small package, `penult`, that depends on these and holds only state, budgets and hand-offs; `article` stays a publishing adapter.

## What already exists (in-house)

| Component | What it covers | Verdict |
|---|---|---|
| `article` [1] | Markdown (footnotes, captions, LaTeX, local images) to an unpublished Substack draft; `--update`, `--dry-run`, tables as code or image; Medium as an Import-a-story step; canonical URLs | depend: the publishing seam |
| `penlike` [2] | per-author, per-register style models; `brief`, `check`, `notes`; now `guide` / `guide-add`, the author-choice guide added for this build (penlike#9) | depend: voice |
| `ductus` [3] | `gauge` with per-segment lean and strength, multi-reader consensus, `baseline` on the author's own texts | depend: machine-sounding passages |
| `illustration` [4] | one `search()` over Openverse and other sources, licence and attribution on every hit | depend: existing images |
| `aix.image.generate_image` [5], `oa.dalle` | paid generation through litellm / OpenAI | depend, behind a budget |
| `falaw` | the woodcut-style generations of the precedent essay | pointer for the generator seam |
| skills `do-research`, `deslop`, `acquaint-write`, `add-references`, `research-topic` | research procedure and prose quality | the skill cites them |
| report: publishing-substack-vs-medium [7] | Substack as primary, Medium by import, the unofficial python-substack route | settled; informs the platform default |
| briefing: the Agile, Reformed process [6] | the fourteen steps actually followed, the user's corrections | the specification |

Not found, after `ir discover packages` and `ir discover skills` in two phrasings each and `projreg search`: any package or skill that takes a seed through research, drafting, voice, images and a review loop. That gap is this package.

## The name

Checked 2026-11-06 with the `short-name-free` script against PyPI and npm: `penult` free on both (also free: `inklings`, `galleyproof`, `penultima`, `firstdraft`, `fromseed`; taken: `galley`, `inkling`, `drafter`, `scrawl`, `essayist`, `scrivener`, `vellum`, `nib`). Chosen for its meaning (the penultimate step, before publication) and its echo of `penlike`.

## REFERENCES

[1] [article: tools to semi-automate the publication of articles](https://github.com/thorwhalen/article)
[2] [penlike: model how an author writes](https://github.com/thorwhalen/penlike)
[3] [ductus: gauge which parts of a text read as machine-written](https://github.com/thorwhalen/ductus)
[4] [illustration: find existing images to illustrate text](https://github.com/thorwhalen/illustration)
[5] [aix: AI utilities, including image generation](https://github.com/thorwhalen/aix)
[6] [Briefing: the Agile, Reformed publishing process](https://github.com/thorwhalen/essays/blob/master/docs/briefings/2026-11-06-agile-reformed-publishing-process.md)
[7] [Where to publish the essay: Substack vs Medium (2026)](https://github.com/thorwhalen/essays/blob/master/docs/The%20Agile%20Religion%20and%20the%20Agentic%20Reformation/publishing-substack-vs-medium.md)
