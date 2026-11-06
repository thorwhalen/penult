# penult.store

Where penult’s private data lives, and the preferences read from it.

Everything a person tells penult about how they want their drafts made is private:
which voices, which platform, how many paid images, where their publishing
credentials are. None of it belongs in a repository. It lives under the data root:

```default
<data root>/config/preferences.json
```

The data root is the `data_dir` argument, else `$PENULT_DATA_DIR`, else
`~/.local/share/penult` (`$XDG_DATA_HOME` and `%LOCALAPPDATA%` are honoured).

Code reaches the files through a `MutableMapping` of relative path to text, so the
local folder can be swapped for any other store (or a plain dict in tests) without
touching the rest:

```pycon
>>> prefs = preferences(files={})
>>> prefs["max_generated_images"], prefs["platform"]
(2, 'substack')
>>> files = {}
>>> set_preference("platform", "medium", files=files)["platform"]
'medium'
>>> preferences(files=files)["platform"]
'medium'
```

### Module Attributes

| [`DEFAULT_PREFERENCES`](#penult.store.DEFAULT_PREFERENCES)   | The preferences every verb falls back to.   |
|------------------------------------------------------------------------|---------------------------------------------|

### Functions

| [`data_dir`](#penult.store.data_dir)([data_dir])                              | The data root: the argument, else `$PENULT_DATA_DIR`, else the user data folder.      |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`preferences`](#penult.store.preferences)(\*[, data_dir, files])                | The preferences: the defaults, overlaid with what the person wrote.                   |
| [`set_preference`](#penult.store.set_preference)(key, value, \*[, data_dir, files]) | Set one preference and return the whole set.                                          |
| [`text_files`](#penult.store.text_files)(root)                                  | A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.              |
| [`write_preferences`](#penult.store.write_preferences)(values, \*[, data_dir, files])  | Replace the saved preferences (only the keys that differ from the defaults are kept). |

### penult.store.DEFAULT_PREFERENCES *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]* *= {'article_env_file': '~/.config/article/.env', 'article_state_path': '~/.local/share/article/pipeline_state.json', 'audience': 'non-technical readers, or software engineers, managers and scientists', 'inset_width': 400, 'max_generated_images': 2, 'min_image_prompts': 5, 'platform': 'substack', 'research_depth': 'deep', 'voice_models': ['me'], 'voice_register': 'essay', 'workspace': 'docs/{slug}'}*

The preferences every verb falls back to. A person changes them with
`penult prefs-set`; an agent changes them only when the person said so.

### penult.store.data_dir(data_dir=None)

The data root: the argument, else `$PENULT_DATA_DIR`, else the user data folder.

```pycon
>>> data_dir("somewhere").is_absolute()
True
```

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### penult.store.preferences(, data_dir=None, files=None)

The preferences: the defaults, overlaid with what the person wrote.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.store.set_preference(key, value, , data_dir=None, files=None)

Set one preference and return the whole set.

`value` must have the type of the default: a number (`2`), a JSON list
(`'["me", "dfw"]'`) or text.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.store.text_files(root)

A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.

Folders are made on write and never on read, and a delete is permanent.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### penult.store.write_preferences(values, , data_dir=None, files=None)

Replace the saved preferences (only the keys that differ from the defaults are kept).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
