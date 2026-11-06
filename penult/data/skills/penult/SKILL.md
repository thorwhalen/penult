---
name: penult
description: Take an idea (a GitHub issue) to a publication draft posted for the author's review, then, once they approve, to an unpublished Substack or Medium draft. Use on "make a draft for <issue url>", "turn this issue into an essay", "write up issue N for Substack", "draft the next essay", "post the draft on the issue", "they approved it, publish the draft", or whenever an essay goes from a seed to a reviewed draft. Drives the whole path with the penult verbs (workspace, state, images within budget, issue comment, publishing hand-off) and the skills that own each step: do-research for checking claims and finding critiques, penlike (and its author-choice guide) and deslop for voice, ductus for machine-sounding passages, illustration for credited images. Posts the draft only where the author asked (the issue thread, public if the repository is); never publishes to a platform, and never sends anything to a platform before the author says the posted draft is good.
license: MIT
metadata:
  audience: users
---

# penult: from a seed to a draft the author can review

The author gives you a seed, usually an issue in their essays repository, and wants back a link to a **draft posted as a comment on that issue**, with images inline, in their voice, every claim checked and the other side of each argument known. They iterate with you there. When they say it is good, you make an **unpublished** platform draft and give them the link; they press Publish themselves. Nothing you do publishes to a platform. The issue comment is as public as the repository is, which is what the author asked for; if the essay must stay private until it is out, say so before posting and ask where the review should happen.

Everything about *how* the author wants this (voices, platform, image budget, where their credentials are) is in their private preferences: `penult prefs`. Everything about *this* essay (the seed, the brief, the research, the draft, the images and their credits, what was posted) is in the workspace that `penult start` makes next to the issue, in `docs/<slug>/` of its repository, so that it is versioned and searchable later.

## The path

```bash
penult start <issue url>          # from inside the repository's checkout; prints the workspace and whether the seed is thin
penult status <workspace>         # at any time: stage, files, what comes next
```

### 1. Seed and brief

Read `seed.md`. Fill the `[DECIDE: ...]` lines of `brief.md`: thesis, angle and shape, audience, voices, platform, visual style. The essay is **never a report** unless the author asked for one: no executive summary, no numbered sections of findings, no bullet lists of evidence. It is an argument, a story and its moral, a debunking, a field guide.

**If `start` says the seed is thin** (few words, no thesis): do not research or draft. Write the author your questions, each with your recommendation (where to take it, what the point is, who it is for, which style), post them as a comment on the issue, record them in `brief.md`, and stop until they answer. A rich seed (a long body, a worked argument, an existing report) gets no questions: decide, write the assumptions into `brief.md`, and go on. Say in the final hand-over what you assumed.

### 2. Research

Load the `do-research` skill, Deep depth. The themes are fixed by the job: **verify every claim the seed makes** (numbers, quotes, attributions, dates), **find the critiques and counter-evidence** so the essay knows both sides, **the standard names** for the things it talks about, and **candidate images**: figures, tables, charts and public-domain art worth using, each with its source and licence. Run the themes as parallel agents; each writes one Vancouver-referenced note into `research/` of the workspace (lowercase filenames, `[name](url)` references, estimates labelled, "unverified" said plainly). Then `penult mark <workspace> --stage researched`. (Every verb below takes the workspace as its first argument or as `--folder`; the examples leave it out for brevity.)

### 3. Draft

Write `essay.md` with front matter (`title:`, `subtitle:`, optional `tags:`), the title again as the one `#` heading, relative image paths (`img/...`) and `[^n]` footnotes where a source matters. Hyperlink sources inline the way the author's published essays do. What the research corrected, correct in the essay; where a claim stays contested, let the essay say so in one sentence rather than hedge everywhere. Keep the author's own sentences from the seed wherever they are there. `penult mark --stage drafted`.

### 4. Voice

Load the `penlike` skill and run `penlike guide`: it is the author's own rule book for which models fit which subject, audience and part of a text, and what not to overdo. Choose the base voice (the `voice_models` preference, usually the author's own model) and at most two other authors from the guide. Then, passage by passage, with the surrounding paragraphs in view so each rewrite still flows:

1. `ductus gauge essay.md` and your own reading mark the spans that sound machine-made (generalising, balanced-for-balance's-sake, tidy lists of three, summary closers). Those get rewritten first, in the base voice (`penlike brief --like <model> --style essay`).
2. The passages the guide reserves for another author (an opening jab, a close, a deadpan debunking) are rewritten in that author's register, short, and only where the subject invites it.
3. The `deslop` skill's passes for rhythm, specificity and ownership; then `penlike check` against the base voice, at most two rounds.

`penult check <workspace>` runs ductus and penlike over the essay and writes a check file under the private data root (it quotes the author's style-model figures, so it never goes into the workspace); read it, but do not chase a zero: human writing is flagged too, and bland prose with no tell is the worse failure. `penult mark --stage styled`.

### 5. Images

For each place an image belongs (the hero, one per major turn of the argument, any figure the research found):

- **Existing images first**: `penult image-search "<what the beat shows>" --folder <workspace>` (the `illustration` package: Openverse, public-domain art, with licence and attribution). Take one with `penult image-add <url> --name <file> --credit "<credit line>" --license <licence>`; the credit goes in the Markdown caption.
- **Prompts**: write at least `min_image_prompts` (default 5) prompts into `images.md`, each saying the beat, the style, the composition. Generate **at most `max_generated_images` (default 2)** of them with `penult image-generate "<prompt>" --name <file>`: the top one or two, chosen for where an image matters most. The budget is deliberate: generated images are paid and often off; the author tries the other prompts by hand and gives you the files (`penult image-add <file> --name ... --credit "Image generated for this essay" --prompt "<the prompt>"`).
- Figures and tables from the research are redrawn (matplotlib, a clean table image) and credited to their source.

Place each image in `essay.md` as its own paragraph: `![alt](img/file.png "Caption with the credit")`, directly after the paragraph that first refers to it (the hero goes under the title, before the first paragraph).

**Layout** (the rules and their sources: `misc/docs/research/2026-11-06-illustration-layout-for-essays.md` in the penult repository). An image at column width that is square or portrait is drawn taller than a laptop screen, which readers resent; so each image has a size class, kept in `essay.md`'s front matter and honoured by the comment (`<img width>`) and by Substack (python-substack's image marker, added at publish time):

- `inset` (about half the column, centred): square and portrait images, atmosphere photographs, a hero that is not landscape;
- `normal` (the column; the default): landscape images, diagrams, charts, a landscape hero;
- `large` and `full`: opt-in only, for an image that is itself the content (a map, a panorama); Substack shows `large` on the web only.

Run `penult layout <workspace>` to see each image's pixels and the class the rules suggest, and `penult layout <workspace> --apply` to write the suggestions into the front matter (a class set by hand is kept). Prefer generating the hero at 16:9 in the first place; a square hero is an inset or gets cropped. Few images: after the hero, at most one per 500-1000 words, each with its own purpose; `layout` notes when there are more. Captions: one line, saying what the image means for the argument, the credit short at the end when a licence or disclosure needs it; no italics in the source (the platforms draw captions small and upright). Alt text always.

`penult mark --stage illustrated`.

### 6. Post the draft

Commit and push the workspace (the comment shows images by their raw GitHub URL, so an unpushed image is a broken picture; `penult post` refuses until they are pushed). Then:

```bash
penult render <workspace>     # writes comment.md: heading, subtitle, absolute images, a footer naming the research folder
penult post <workspace>       # posts it; a second run updates the same comment (--new for another)
```

Give the author the comment link. Iterate on their comments: edit `essay.md`, re-run the voice checks that matter (and `layout` if images changed), `render`, `post`. Record anything they say about voice or images that should hold for later essays with `penlike guide-add "<one line>" --source <issue url>` or `penult prefs-set`.

### 7. Approval, then the platform draft

Only when the author says the posted draft is good, in their words:

```bash
penult approve <workspace> --by <who> --note "<their words>"   # of the text as posted; a later edit needs a new post and approval
penult publish <workspace>               # substack by default: an UNPUBLISHED draft via `article draft-substack`; prints the editor link
penult publish <workspace> --dry-run     # what Substack would lose (tables, inline images), no credentials needed
```

`publish` uses the `article` package with the credentials file named in the preferences (`article_env_file`), never a credential in a repository. Medium is article's Import-a-story step and comes after the Substack post is live. Hand the author the editor link; they review and publish. You do not.

## Hand-over, every time

Say: the comment or draft link; which voices were used for which passages and why (from the guide); what the research corrected in the seed; the images used and their credits; the prompts left for the author to try; what you assumed where the seed was silent; and anything the author must do (a credential, an approval, the Publish button).

## Never

- Publish, schedule, or send anything to readers. The platform step makes a draft and stops.
- Put a model, a preference, a credential, or anything from `~/.local/share/penlike` or `~/.local/share/penult` into a repository, an issue or a commit.
- Spend past the image budget without the author asking, or present a generated image as a photograph.
- Invent a fact, a number, a quote or a source to fill a gap. A gap is a question, written `[ASK: ...]` in the draft and asked.
- Turn the essay into a report, or sand off the author's opinions into balance.
