# penult.workspace

One essay’s workspace: its files, its state, and the seed and brief written into it.

A workspace is a folder, by default `docs/<slug>/` inside the issue’s repository,
so that the research notes, the essay and its images are versioned next to the
issue they came from and found by whoever indexes that repository’s docs:

```default
<workspace>/
    penult.json      state: the issue, the stage, the images, the comment, the draft
    seed.md          the issue as fetched: title, body, comments
    brief.md         angle, audience, voice, platform, image budget, assumptions
    research/        the research notes (Vancouver references), one file per theme
    essay.md         the draft, with front matter for title and subtitle
    images.md        every image candidate and prompt, with credit and licence
    img/             the images the essay uses
    comment.md       the essay rendered for an issue comment
```

The style check (`penult check`) is written under the private data root, not
here: it quotes figures from the author’s private style models.

```pycon
>>> ws = Workspace("/tmp/x/docs/an-essay")
>>> ws.essay.name, ws.state_file.name
('essay.md', 'penult.json')
```

### Functions

| [`is_thin`](#penult.workspace.is_thin)(issue, \*[, threshold])   | Whether the seed is too thin to research and draft from without asking.   |
|------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`slug_of`](#penult.workspace.slug_of)(title, \*[, max_length])  | A folder-safe slug from a title, cut at a word boundary.                  |
| [`word_count`](#penult.workspace.word_count)(text)                  | How many whitespace-separated words a text has.                           |

### Classes

| [`Workspace`](#penult.workspace.Workspace)(folder)   | The folder of one essay and the files in it.   |
|----------------------------------------------------------------------|------------------------------------------------|

### *class* penult.workspace.Workspace(folder)

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
  [`Workspace`](#penult.workspace.Workspace)

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

### penult.workspace.is_thin(issue, , threshold=250)

Whether the seed is too thin to research and draft from without asking.

A thin seed is one with fewer than `threshold` words in title, body and
comments together. The result says why, so the agent can quote it in the
questions it sends.

```pycon
>>> is_thin({"title": "An idea", "body": "Agents read specs.", "comments": []})["thin"]
True
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.workspace.slug_of(title, , max_length=60)

A folder-safe slug from a title, cut at a word boundary.

```pycon
>>> slug_of("AI and the Accretion Trap: Why Experts Underestimate Broken Technologies")
'ai-and-the-accretion-trap-why-experts-underestimate-broken'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.workspace.word_count(text)

How many whitespace-separated words a text has.

```pycon
>>> word_count("one two  three\nfour")
4
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
