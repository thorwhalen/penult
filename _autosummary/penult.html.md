# penult

penult: from an idea to a publication draft, posted where its author can review it.

The seed is a GitHub issue. penult fetches it into a workspace next to it, holds the
brief, the research notes, the essay, the images and their credits, checks the draft
with ductus and penlike, renders it as an issue comment, and, once the author says
so, hands it to `article` for an unpublished Substack or Medium draft. The
thinking in between (research, drafting, the style passes) is an agent’s, laid out
in the `penult` skill; the verbs here keep every step from being improvised twice.

```pycon
>>> import penult
>>> penult.prefs(files={})["preferences"]["platform"]
'substack'
```

### Functions

| [`approve`](#penult.approve)([folder, by, note])                        | Record that the person is happy with the posted draft, as it stands now; this lets `publish` run.   |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`check`](#penult.check)([folder, like, style, out, data_dir, ...])   | Read the essay with ductus and penlike, and write what they found to a private check file.          |
| [`data_dir`](#penult.data_dir)([data_dir])                               | The data root: the argument, else `$PENULT_DATA_DIR`, else the user data folder.                    |
| [`image_add`](#penult.image_add)(source, \*, name, credit[, folder, ...]) | Add an image (a URL or a local file) to img/ with its credit; `--prompt` if a person generated it.  |
| [`image_generate`](#penult.image_generate)(prompt, \*, name[, folder, ...])    | Generate one image from `prompt` into img/, within the `max_generated_images` budget.               |
| [`image_search`](#penult.image_search)(query, \*[, folder, n, searcher])     | Find existing stock, Creative-Commons or public-domain images for `query`, credited.                |
| [`layout`](#penult.layout)([folder, apply])                            | Each image's size class against the layout rules; `--apply` writes the suggestions.                 |
| [`mark`](#penult.mark)([folder])                                     | Record that the workspace reached `stage` (researched, drafted, styled, illustrated).               |
| [`post`](#penult.post)([folder, new, runner])                        | Post comment.md on the issue (or update the comment posted last time; `--new` posts another).       |
| [`preferences`](#penult.preferences)(\*[, data_dir, files])                 | The preferences: the defaults, overlaid with what the person wrote.                                 |
| [`prefs`](#penult.prefs)(\*[, data_dir, files])                       | The private preferences (defaults overlaid with what the person set).                               |
| [`prefs_set`](#penult.prefs_set)(key, value, \*[, data_dir, files])       | Set one preference; the value must have the default's type (`2`, `'["me","dfw"]'`, text).           |
| [`publish`](#penult.publish)([folder, platform, dry_run, ...])          | Hand the approved essay to the publisher for an **unpublished** draft on the platform.              |
| [`render`](#penult.render)([folder, raw_base, data_dir, files, ...])   | Write comment.md: the essay as a GitHub comment, relative images turned into raw URLs.              |
| [`start`](#penult.start)(seed, \*[, into, force, data_dir, ...])      | Fetch the seed (a GitHub issue URL) and make the workspace: seed, brief, state.                     |
| [`status`](#penult.status)([folder])                                   | Where the workspace stands: stage, files present, images, the posted comment, what comes next.      |

### Classes

| [`Workspace`](#penult.Workspace)(folder)   | The folder of one essay and the files in it.   |
|----------------------------------------------------------------------|------------------------------------------------|

### Exceptions

| [`PenultError`](#penult.PenultError)   | An error whose message says what to do next.   |
|----------------------------------------------------------------|------------------------------------------------|

### *exception* penult.PenultError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message says what to do next.

### *class* penult.Workspace(folder)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The folder of one essay and the files in it.

#### advance(stage)

Move to `stage` unless the workspace is already past it.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### exists()

Whether this folder was started by penult.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### files_present()

Which of the expected files exist, with word counts where that means something.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### read_state()

The state, `{}` before the workspace is started.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### require()

This workspace, or an error saying how to start one.

* **Return type:**
  [`Workspace`](penult.workspace.html.md#penult.workspace.Workspace)

#### *property* state_file *: [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path)*

The state file.

#### update_state(\*\*changes)

Merge `changes` into the state and return it.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### write_state(state)

Replace the state.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### penult.approve(folder=None, , by='the user', note='')

Record that the person is happy with the posted draft, as it stands now; this lets `publish` run.

Only set it when the person said so, in their words; quote them in `--note`. The
approval is of this text: if essay.md changes afterwards, `publish` refuses until
the person approves again.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.check(folder=None, \*, like=None, style=None, out=None, data_dir=None, files=None, runner=<function run>)

Read the essay with ductus and penlike, and write what they found to a private check file.

ductus marks the segments that read machine-made (lean toward +1, with the
evidence strength); penlike measures the draft against each voice model in
`like` (the `voice_models` preference by default). The report quotes figures
from the author’s private style models, so it goes under the data root
(`work/<slug>/check.md`), not into the workspace, unless `out` says where.
The agent’s own reading comes on top of this; neither tool sees bland prose that
carries no tell.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.data_dir(data_dir=None)

The data root: the argument, else `$PENULT_DATA_DIR`, else the user data folder.

```pycon
>>> data_dir("somewhere").is_absolute()
True
```

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### penult.image_add(source, , name, credit, folder=None, license='', prompt=None)

Add an image (a URL or a local file) to img/ with its credit; `--prompt` if a person generated it.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.image_generate(prompt, , name, folder=None, force=False, data_dir=None, files=None, generator=None)

Generate one image from `prompt` into img/, within the `max_generated_images` budget.

Past the budget the prompt is only recorded in images.md, for the person to try
by hand; `--force` spends one more because the person asked.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.image_search(query, , folder=None, n=8, searcher=None)

Find existing stock, Creative-Commons or public-domain images for `query`, credited.

Candidates are recorded in images.md. Download the one you use with
`image-add <url> --name <file> --credit "<the credit line shown>"`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.layout(folder=None, , apply=False)

Each image’s size class against the layout rules; `--apply` writes the suggestions.

The rules (`penult.figures`, from the layout research in `misc/docs/research/`):
the hero is landscape at column width or an inset; a square or portrait body image
is an inset; a landscape one, a diagram or a chart takes the column; after the hero,
about one image per 500 words at most. The class goes in essay.md’s `images:`
front matter, which `render` honours as `<img width>` and `publish` as
python-substack’s image marker. `--apply` sets every unset image’s class to the
suggestion (a class set by hand is kept; to change one, edit the front matter).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.mark(folder=None, , stage)

Record that the workspace reached `stage` (researched, drafted, styled, illustrated).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.post(folder=None, \*, new=False, runner=<function run>)

Post comment.md on the issue (or update the comment posted last time; `--new` posts another).

Refuses while comment.md is older than essay.md, while an image the essay shows is
missing, and while any image is not committed and pushed, since its raw URL would
be a 404 for the reader.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.preferences(, data_dir=None, files=None)

The preferences: the defaults, overlaid with what the person wrote.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.prefs(, data_dir=None, files=None)

The private preferences (defaults overlaid with what the person set).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.prefs_set(key, value, , data_dir=None, files=None)

Set one preference; the value must have the default’s type (`2`, `'["me","dfw"]'`, text).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.publish(folder=None, \*, platform=None, dry_run=False, data_dir=None, files=None, runner=<function run>, publisher=None)

Hand the approved essay to the publisher for an **unpublished** draft on the platform.

The default publisher is the `article` package (Substack draft, or Medium’s
import step); the draft’s editor link comes back and the person publishes by
hand. Refuses before `penult approve`, and after any change to essay.md since
the approval, unless `--dry-run` (which converts and checks, sending nothing).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.render(folder=None, \*, raw_base=None, data_dir=None, files=None, runner=<function run>)

Write comment.md: the essay as a GitHub comment, relative images turned into raw URLs.

`raw_base` is worked out from the checkout (owner, repo, commit, folder) when
not given; pinning the commit keeps the links alive after the branch is merged.
The comment ends with a footer naming the seed and the research folder.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.start(seed, \*, into=None, force=False, data_dir=None, files=None, fetch=None, runner=<function run>)

Fetch the seed (a GitHub issue URL) and make the workspace: seed, brief, state.

The workspace goes `into` the folder given, else to the `workspace` preference
(`docs/<slug>` by default) inside the checkout of the issue’s own repository
that holds the current directory. A thin seed (few words, no thesis) is reported
so the agent asks the user before researching. `--force` refetches the seed into
an existing workspace; the brief and the stage are kept.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penult.status(folder=None)

Where the workspace stands: stage, files present, images, the posted comment, what comes next.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Modules

| [`base`](penult.base.html.md#module-penult.base)           | Errors, constants and the stage names shared across penult.                                        |
|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| [`figures`](penult.figures.html.md#module-penult.figures)     | Illustration layout: how big each image is drawn, and where, on every renderer.                    |
| [`github`](penult.github.html.md#module-penult.github)       | GitHub, through the `gh` and `git` commands: read an issue, post or edit a comment, find raw URLs. |
| [`images`](penult.images.html.md#module-penult.images)       | Images for the essay: find existing ones, generate a few, and keep the ledger.                     |
| [`store`](penult.store.html.md#module-penult.store)         | Where penult's private data lives, and the preferences read from it.                               |
| [`tools`](penult.tools.html.md#module-penult.tools)         | The verbs: plain functions, JSON-ready in and out, the one list every surface is built from.       |
| [`workspace`](penult.workspace.html.md#module-penult.workspace) | One essay's workspace: its files, its state, and the seed and brief written into it.               |
