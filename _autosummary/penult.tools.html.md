# penult.tools

The verbs: plain functions, JSON-ready in and out, the one list every surface is built from.

An agent drives an essay from a seed to a reviewed draft with these, in this order:

```default
start      fetch the seed (a GitHub issue), make the workspace, say whether it is thin
status     where the workspace stands and what comes next
mark       record a stage reached by the agent's own work (researched, drafted, ...)
check      ductus and penlike over the essay: what still reads machine-made or off-voice
image-search / image-generate / image-add   images, within the budget, all credited
render     the essay as an issue comment, images as raw URLs pinned to the commit
post       post (or update) that comment on the issue
approve    record that the person is happy with the posted draft, as it was then
publish    hand the approved essay to ``article`` for an unpublished platform draft
prefs / prefs-set   the private preferences
```

The thinking (research, drafting, the style passes) is the agent’s and is laid out
in the `penult` skill; these verbs hold the state, the files, the budget and the
hand-offs so that no step is improvised twice. Nothing here prints or exits: the
command line and any other surface wrap [`TOOLS`](#penult.tools.TOOLS).

### Module Attributes

| [`HIDDEN_PARAMETERS`](#penult.tools.HIDDEN_PARAMETERS)   | the in-memory store and the injected callables are for Python callers and tests.   |
|----------------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`TOOLS`](#penult.tools.TOOLS)               | The one list every surface is built from.                                          |

### Functions

| [`without`](#penult.tools.without)(func[, hidden])   | The same verb with `hidden` parameters removed from its signature.   |
|----------------------------------------------------------------------------|----------------------------------------------------------------------|

### penult.tools.HIDDEN_PARAMETERS *= ('files', 'fetch', 'runner', 'searcher', 'generator', 'publisher')*

the in-memory store and
the injected callables are for Python callers and tests.

* **Type:**
  Parameters a surface built from these signatures leaves out

### penult.tools.TOOLS *= [<function start>, <function status>, <function mark>, <function check>, <function image_search>, <function image_generate>, <function image_add>, <function layout>, <function render>, <function post>, <function approve>, <function publish>, <function prefs>, <function prefs_set>]*

The one list every surface is built from. Never write a second one.

### penult.tools.without(func, hidden=('files', 'fetch', 'runner', 'searcher', 'generator', 'publisher'))

The same verb with `hidden` parameters removed from its signature.

```pycon
>>> "files" in inspect.signature(without(prefs)).parameters
False
```

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)
