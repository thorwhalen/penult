# penult.figures

Illustration layout: how big each image is drawn, and where, on every renderer.

The rules come from `misc/docs/research/2026-11-06-illustration-layout-for-essays.md`
(sourced where it could be, judgment where it says so). The short version:

- An image has a **size class**: `inset` (about half the column, centred), `normal`
  (the column, the default), `large` (wider than the column; Substack renders it on
  the web only) or `full` (edge to edge; opt-in, for an image that *is* the content).
  The vocabulary mirrors what Substack, Medium and the Guardian’s renderer already have.
- The **hero** (the first image, under the title) is landscape at column width, or an
  inset. A square or portrait image at column width is drawn taller than a laptop
  screen, which is the complaint this module exists to answer.
- A body image that is square or portrait is an inset; a landscape one, a diagram or a
  chart is `normal`. Few images: after the hero, at most one per 500-1000 words.
- Captions are one line, not italic (the platforms draw them small, centred, upright).

The class lives in the essay’s front matter, out of the Markdown that goes to the
publisher:

```default
images:
  img/hero.png: inset
```

A GitHub comment honours it as `<img width>`; python-substack honours it through its
own `<!-- python-substack-image:v1 ... -->` marker, which [`substack_markdown()`](#penult.figures.substack_markdown)
writes after each sized image. Neither `{width=...}` nor `<img>` may go to
python-substack (the first turns the image into its alt text, the second drops it).

```pycon
>>> sizes_from_fields({"images": {"img/a.png": "inset"}})
{'img/a.png': 'inset'}
>>> suggest_size(1024, 1024, hero=True)
('inset', 'square hero: at column width it is taller than a laptop screen')
>>> suggest_size(1456, 819, hero=True)
('normal', 'landscape hero (16:9) fits the column')
```

### Module Attributes

| [`SIZES`](#penult.figures.SIZES)          | The size classes, narrowest first.                                                                                                     |
|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| [`COLUMN_WIDTH`](#penult.figures.COLUMN_WIDTH)   | Substack's post column, in CSS pixels (measured; the research report, section 2).                                                      |
| [`INSET_WIDTH`](#penult.figures.INSET_WIDTH)    | a little over half the column, inside the Guardian's "supporting" range and Wikipedia's 400 px ceiling.                                |
| [`GITHUB_ATTRS`](#penult.figures.GITHUB_ATTRS)   | `<img>` attributes per class for a GitHub comment (the comment is already about the column's width, so only `inset` narrows anything). |
| [`SUBSTACK_ATTRS`](#penult.figures.SUBSTACK_ATTRS) | `image2` attributes per class for python-substack.                                                                                     |

### Functions

| [`describe_images`](#penult.figures.describe_images)(folder, markdown)                 | One record per image: path, pixels, the class set, the class suggested, the reason.   |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`github_attrs`](#penult.figures.github_attrs)(size, \*[, inset_width])             | The `<img>` attributes a size class adds in a GitHub comment.                         |
| [`pixel_size`](#penult.figures.pixel_size)(path)                                  | `(width, height)` of a PNG, GIF or JPEG from its header, else `None`.                 |
| [`sizes_from_fields`](#penult.figures.sizes_from_fields)(fields)                         | The `images:` front-matter map, validated: relative path -> size class.               |
| [`substack_markdown`](#penult.figures.substack_markdown)(markdown[, sizes, inset_width]) | The essay with a python-substack image marker after each image whose class says so.   |
| [`suggest_size`](#penult.figures.suggest_size)(width, height, \*, hero)             | The size class the rules give an image of these pixels, with the reason.              |
| [`with_sizes`](#penult.figures.with_sizes)(markdown, sizes)                       | The essay text with its `images:` front-matter map replaced by `sizes`.               |

### penult.figures.COLUMN_WIDTH *= 728*

Substack’s post column, in CSS pixels (measured; the research report, section 2).

### penult.figures.GITHUB_ATTRS *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]]* *= {'full': {}, 'inset': {'width': 400}, 'large': {}, 'normal': {}}*

`<img>` attributes per class for a GitHub comment (the comment is already about
the column’s width, so only `inset` narrows anything).

### penult.figures.INSET_WIDTH *= 400*

a little over half the
column, inside the Guardian’s “supporting” range and Wikipedia’s 400 px ceiling.

* **Type:**
  An inset’s rendered width, in CSS pixels, on both renderers

### penult.figures.SIZES *= ('inset', 'normal', 'large', 'full')*

The size classes, narrowest first.

### penult.figures.SUBSTACK_ATTRS *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]]* *= {'full': {'fullscreen': True}, 'inset': {'resizeWidth': 400}, 'large': {'imageSize': 'large'}, 'normal': {}}*

`image2` attributes per class for python-substack. `resizeWidth` is what the
editor’s own resize handle writes. `large` and `full` are the values the
stylesheet’s `sizing-large` / `sizing-fullscreen` classes imply; a draft sized
in the editor and read back would confirm them (the report’s open item).

### penult.figures.describe_images(folder, markdown)

One record per image: path, pixels, the class set, the class suggested, the reason.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penult.figures.github_attrs(size, , inset_width=400)

The `<img>` attributes a size class adds in a GitHub comment.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.figures.pixel_size(path)

`(width, height)` of a PNG, GIF or JPEG from its header, else `None`.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### penult.figures.sizes_from_fields(fields)

The `images:` front-matter map, validated: relative path -> size class.

```pycon
>>> sizes_from_fields({})
{}
>>> sizes_from_fields({"images": {"img/a.png": "huge"}})
Traceback (most recent call last):
...
penult.base.PenultError: images: img/a.png: unknown size 'huge'; one of inset, normal, large, full
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### penult.figures.substack_markdown(markdown, sizes=None, , inset_width=400)

The essay with a python-substack image marker after each image whose class says so.

The marker is an HTML comment python-substack merges into the `image2` node;
GitHub and every Markdown viewer hide it. Front matter and the image lines are
unchanged, so `article`’s checks apply as before.

```pycon
>>> out = substack_markdown('---\ntitle: T\nimages:\n  img/a.png: inset\n---\n# T\n\n![a](img/a.png "c")\n')
>>> out.splitlines()[-1].startswith("<!-- python-substack-image:v1 ")
True
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.figures.suggest_size(width, height, , hero)

The size class the rules give an image of these pixels, with the reason.

```pycon
>>> suggest_size(709, 195, hero=False)
('normal', 'landscape (3.6:1) at column width')
>>> suggest_size(700, 556, hero=False)
('inset', 'squarish (1.3:1): an inset keeps the text in view')
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### penult.figures.with_sizes(markdown, sizes)

The essay text with its `images:` front-matter map replaced by `sizes`.

Only the `images` key changes; the other front-matter lines are kept as written.

```pycon
>>> print(with_sizes('---\ntitle: T\n---\nbody\n', {"img/a.png": "inset"}))
---
title: T
images:
  img/a.png: inset
---
body
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
