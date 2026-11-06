# penult.images

Images for the essay: find existing ones, generate a few, and keep the ledger.

Three sources, one ledger (`images.md` in the workspace, mirrored in the state):

- **search**: existing stock, Creative-Commons and public-domain images through the
  `illustration` package, which carries licence and attribution with each hit;
- **generate**: a paid image from a prompt through `aix.image.generate_image`,
  capped by the person’s `max_generated_images` so that an off prompt does not
  cost much; every prompt is kept in the ledger whether or not it was run;
- **add**: an image the person made or found themselves, with its credit.

The searcher and the generator are seams: any callable of the same shape works, and
tests pass fakes.

```pycon
>>> credit_line({"title": "Harbour", "author": "A. Painter", "license": "cc-by", "source": "openverse"})
'Harbour, by A. Painter (cc-by, via openverse)'
```

### Functions

| [`add_image`](#penult.images.add_image)(ws, source, \*, name, credit[, ...])   | Put an image in `img/` (from a URL or a local path) and record its credit.           |
|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`credit_line`](#penult.images.credit_line)(record)                              | A one-line credit from a record: the attribution if the source gave one, else built. |
| [`default_generator`](#penult.images.default_generator)(prompt, \*, path, \*\*options) | Generate one image with `aix` (DALL-E 3 and other litellm providers) and save it.    |
| [`default_searcher`](#penult.images.default_searcher)(query, \*[, n])                 | The `illustration` package's unified search (Openverse by default, no key needed).   |
| [`generate_image`](#penult.images.generate_image)(ws, prompt, \*, name, ...[, ...]) | Generate one image from `prompt` into `img/`, within the budget.                     |
| [`search_images`](#penult.images.search_images)(ws, query, \*[, n, searcher])      | Find existing images for `query` and record the candidates in the ledger.            |

### penult.images.add_image(ws, source, , name, credit, license='', prompt=None, used=True)

Put an image in `img/` (from a URL or a local path) and record its credit.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### penult.images.credit_line(record)

A one-line credit from a record: the attribution if the source gave one, else built.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.images.default_generator(prompt, , path, \*\*options)

Generate one image with `aix` (DALL-E 3 and other litellm providers) and save it.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### penult.images.default_searcher(query, , n=8, \*\*options)

The `illustration` package’s unified search (Openverse by default, no key needed).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.images.generate_image(ws, prompt, , name, max_generated, force=False, generator=None, \*\*options)

Generate one image from `prompt` into `img/`, within the budget.

The budget counts images this workspace generated automatically. Past it, the
prompt is recorded for the person to try by hand and nothing is spent, unless
`force` is set (the person asked for this one).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.images.search_images(ws, query, , n=8, searcher=None, \*\*options)

Find existing images for `query` and record the candidates in the ledger.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]
