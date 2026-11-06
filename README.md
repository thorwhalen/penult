# penult

From an idea to a publication draft: the penultimate step, where the essay exists, is illustrated, sounds like its author, and waits for them to say go.

```bash
pip install penult
```

The seed is a GitHub issue. An agent, with the `penult` skill, turns it into an essay posted as a comment on that issue for the author to review, and, once the author approves, into an **unpublished** Substack or Medium draft through [article](https://github.com/thorwhalen/article). penult never publishes anything itself.

```bash
penult start https://github.com/you/essays/issues/30     # workspace docs/<slug>/ in the repo: seed.md, brief.md, state
penult status docs/<slug>                                 # stage, files, what comes next
penult check docs/<slug>                                  # ductus (machine-sounding passages) + penlike (voice) over essay.md
penult image-search "a 1995 modem" --folder docs/<slug>   # credited stock / public-domain candidates
penult image-generate "<prompt>" --name hero --folder docs/<slug>   # at most 2 automatically; prompts past that are kept for you
penult render docs/<slug> && penult post docs/<slug>      # the essay as an issue comment, images by raw URL
penult approve docs/<slug> --note "good to go"            # the author's words; this gates publishing
penult publish docs/<slug>                                # an unpublished Substack draft; you press Publish
```

## What penult holds, and what the agent does

The thinking is the agent's: the research that checks every claim and finds the critiques, the draft, the passes that make it sound like the author. The `penult` skill lays that out and names the skills that own each step (`do-research`, `penlike` and its author-choice guide, `deslop`, `ductus`, `illustration`).

penult holds what should not be improvised twice:

- **the workspace**: `docs/<slug>/` next to the issue, with the seed as fetched, the brief (angle, audience, voice, platform, image budget, assumptions), the research notes, `essay.md`, `images.md` with every candidate, prompt and credit, `img/`, and a state file;
- **the thin-seed gate**: a seed with no thesis or too few words is reported, and the agent asks the author before researching;
- **the image budget**: paid generation capped per essay (two by default); every prompt is kept so the author can try the rest by hand;
- **the review loop**: the essay rendered for a GitHub comment (title, subtitle, images turned into raw URLs, captions kept), posted and updated in place, refusing while an image is not pushed;
- **the approval gate**: `publish` runs only after `approve`, and only makes a draft.

## Your preferences stay private

Voices, platform, image budget, where the `article` credentials file is: `penult prefs` shows them, `penult prefs-set <key> <value>` changes one. They live under `~/.local/share/penult` (set `PENULT_DATA_DIR` to move it), never in a project folder. Credentials are never read by penult itself; `publish` hands the path of the credentials file to `article`.

| Preference | Default | Meaning |
|---|---|---|
| `voice_models` | `["me"]` | the penlike models the style pass writes with; the first is the base voice |
| `voice_register` | `essay` | the penlike register to measure against |
| `audience` | non-technical readers, or software engineers, managers and scientists | narrowed per essay in the brief |
| `platform` | `substack` | where `publish` sends the approved essay (`substack` or `medium`) |
| `max_generated_images` | `2` | paid images generated automatically per essay |
| `min_image_prompts` | `5` | prompts the agent writes into `images.md` |
| `article_env_file` | `~/.config/article/.env` | the `article` credentials file |
| `article_state_path` | `~/.local/share/article/pipeline_state.json` | the `article` state file |
| `workspace` | `docs/{slug}` | where a workspace goes in the issue's repository |
| `research_depth` | `deep` | the `do-research` depth |

## From Python

Every command is a function in `penult.tools`, taking and returning JSON-ready values. The in-memory store (`files=`), the issue fetcher (`fetch=`), the command runner (`runner=`), the image searcher and generator (`searcher=`, `generator=`) are keyword arguments, which is how the tests run without a network:

```python
import penult
started = penult.start("https://github.com/you/essays/issues/30", into="docs/my-essay")
penult.image_generate("a woodcut of a modem", name="hero", folder="docs/my-essay")
penult.render("docs/my-essay"); penult.post("docs/my-essay")
```

## Install the skill

```bash
gh skill install thorwhalen/penult penult --agent claude-code
```

The skill is in `penult/data/skills/penult/` and ships with the package.

## Related

- [article](https://github.com/thorwhalen/article): Markdown to an unpublished Substack draft, and syndication with canonical URLs. penult's publishing step.
- [penlike](https://github.com/thorwhalen/penlike): how an author writes, and the author-choice guide (`penlike guide`).
- [ductus](https://github.com/thorwhalen/ductus): which passages read as machine-written, and why.
- [illustration](https://github.com/thorwhalen/illustration): existing images with licence and attribution.
