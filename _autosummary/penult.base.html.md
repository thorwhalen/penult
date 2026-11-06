# penult.base

Errors, constants and the stage names shared across penult.

penult takes a seed (a GitHub issue) to a publication draft posted for review. The
stages below name where a workspace stands; every verb reads and advances them
through the workspace state file, and nothing here depends on any other module.

### Module Attributes

| [`THIN_SEED_WORDS`](#penult.base.THIN_SEED_WORDS)   | A seed with fewer words than this (title, body and comments together) is "thin": the agent asks the user where to take it before researching or drafting.   |
|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`STAGES`](#penult.base.STAGES)            | The stages a workspace moves through, in order.                                                                                                             |

### Functions

| [`stage_index`](#penult.base.stage_index)(stage)   | Where a stage sits in [`STAGES`](#penult.base.STAGES); unknown stages sort first.   |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|

### Exceptions

| [`PenultError`](#penult.base.PenultError)   | An error whose message says what to do next.   |
|----------------------------------------------------------------|------------------------------------------------|

### *exception* penult.base.PenultError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message says what to do next.

### penult.base.STAGES *= ('seeded', 'researched', 'drafted', 'styled', 'illustrated', 'posted', 'approved', 'published')*

The stages a workspace moves through, in order. `approved` is set by the user
(or by the agent relaying the user’s words) and gates `published`.

### penult.base.THIN_SEED_WORDS *= 250*

A seed with fewer words than this (title, body and comments together) is “thin”:
the agent asks the user where to take it before researching or drafting.

### penult.base.stage_index(stage)

Where a stage sits in [`STAGES`](#penult.base.STAGES); unknown stages sort first.

```pycon
>>> stage_index("drafted") > stage_index("seeded")
True
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
