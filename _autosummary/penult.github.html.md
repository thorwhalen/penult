# penult.github

GitHub, through the `gh` and `git` commands: read an issue, post or edit a comment, find raw URLs.

Every function takes a `runner` (the shape of [`subprocess.run()`](https://docs.python.org/3/library/subprocess.html#subprocess.run)) so tests
run without a network and another transport can be dropped in. The default needs
an authenticated `gh`.

```pycon
>>> parse_issue_url("https://github.com/octo/essays/issues/30")
('octo', 'essays', 30)
```

### Functions

| [`edit_comment`](#penult.github.edit_comment)(comment_url, body_file, \*[, runner])   | Replace an existing comment's body (`comment_url` ends in `#issuecomment-<id>`).        |
|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| [`fetch_issue`](#penult.github.fetch_issue)(url, \*[, runner])                       | The issue's title, body, labels and comments, as one JSON-ready dict.                   |
| [`parse_issue_url`](#penult.github.parse_issue_url)(url)                                 | `(owner, repo, number)` from an issue URL, or an error that shows the shape.            |
| [`post_comment`](#penult.github.post_comment)(url, body_file, \*[, runner])           | Post a file's content as a comment on the issue; returns the comment's URL.             |
| [`raw_url_base`](#penult.github.raw_url_base)(checkout, folder)                       | The `raw.githubusercontent.com` prefix for files in `folder` at the checkout's commit.  |
| [`repo_of_checkout`](#penult.github.repo_of_checkout)(path, \*[, runner])                 | The checkout holding `path`: its root, GitHub owner/repo, branch and commit, or `None`. |
| [`unpushed`](#penult.github.unpushed)(checkout, paths, \*[, runner])              | Which of `paths` are not yet committed and pushed to the branch's upstream.             |

### penult.github.edit_comment(comment_url, body_file, \*, runner=<function run>)

Replace an existing comment’s body (`comment_url` ends in `#issuecomment-<id>`).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.github.fetch_issue(url, \*, runner=<function run>)

The issue’s title, body, labels and comments, as one JSON-ready dict.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penult.github.parse_issue_url(url)

`(owner, repo, number)` from an issue URL, or an error that shows the shape.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### penult.github.post_comment(url, body_file, \*, runner=<function run>)

Post a file’s content as a comment on the issue; returns the comment’s URL.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.github.raw_url_base(checkout, folder)

The `raw.githubusercontent.com` prefix for files in `folder` at the checkout’s commit.

The commit, not the branch, so the links keep working after the branch is
merged and deleted.

```pycon
>>> raw_url_base({"root": "/r", "owner": "o", "repo": "e", "branch": "main", "sha": "abc123"}, Path("/r/docs/an essay"))
'https://raw.githubusercontent.com/o/e/abc123/docs/an%20essay/'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penult.github.repo_of_checkout(path, \*, runner=<function run>)

The checkout holding `path`: its root, GitHub owner/repo, branch and commit, or `None`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### penult.github.unpushed(checkout, paths, \*, runner=<function run>)

Which of `paths` are not yet committed and pushed to the branch’s upstream.

A raw URL only works for a file that is on GitHub, so `post` refuses while any
image it references is in this list. Paths are compared in git’s own form
(forward slashes, unescaped thanks to `-z`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
