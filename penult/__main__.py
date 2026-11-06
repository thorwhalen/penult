# PYTHON_ARGCOMPLETE_OK
"""``penult`` on the command line: every verb of :data:`penult.tools.TOOLS`.

    penult start https://github.com/<owner>/essays/issues/30
    penult status docs/<slug>
    penult check docs/<slug>
    penult image-search "a 1990s modem" --folder docs/<slug>
    penult render docs/<slug> && penult post docs/<slug>
    penult approve docs/<slug> --note "looks good, ship it"
    penult publish docs/<slug>

``--json`` anywhere prints the whole result instead of its text. The exit status is 0
when the result is ok and 1 when it is not.
"""

from __future__ import annotations

import functools
import json
import sys

import cw

from penult import tools
from penult.base import PenultError


def _command(func):
    func = tools.without(func)

    @functools.wraps(func)
    def command(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PenultError as error:
            raise cw.CommandError(str(error)) from error

    return command


def _egress(as_json):
    def egress(result, *, out, err):
        if as_json or not isinstance(result, dict):
            print(
                json.dumps(result, indent=2, ensure_ascii=False, default=str), file=out
            )
        else:
            print(result.get("text") or result.get("summary") or "", file=out)
        return 0 if not isinstance(result, dict) or result.get("ok", True) else 1

    return egress


def main(argv=None):
    """Run the command line. The ``penult`` console script."""
    for stream in (sys.stdout, sys.stderr):
        getattr(stream, "reconfigure", lambda **_: None)(errors="backslashreplace")
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    commands = {f.__name__.replace("_", "-"): _command(f) for f in tools.TOOLS}
    code = cw.dispatch(
        commands,
        [a for a in argv if a != "--json"],
        prog="penult",
        convention=cw.MODERN,
        egress=_egress(as_json),
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
