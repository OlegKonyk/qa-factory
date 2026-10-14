"""The environment every check gives a subprocess that runs the application's interpreter or a tool
installed beside it (pytest, ruff, mutmut).

Two facts measured on an application with a `src/` layout (2026-10-14, `docs/log.md`):

- Its tests ran `alembic` as a subprocess and failed with `FileNotFoundError` because the
  environment's bin folder was not on PATH (its own runner, nox, puts it there). The interpreter's
  folder goes first on PATH here.
- mutmut 3.8.0 on macOS: every mutant child crashed with SIGSEGV in urllib's macOS proxy lookup
  (`_scproxy`, not safe after fork) unless a `*_proxy` variable was set. `no_proxy='*'` makes
  urllib skip the lookup; it is set for mutmut when no proxy variable is set, on every platform.
"""

import os

PROXY_VARS = (
    "no_proxy",
    "NO_PROXY",
    "http_proxy",
    "HTTP_PROXY",
    "https_proxy",
    "HTTPS_PROXY",
    "all_proxy",
    "ALL_PROXY",
)


def app_env(python, *, mutmut=False, **extra) -> dict[str, str]:
    """The environment for a subprocess that runs the application's interpreter or a tool from
    its environment: a copy of os.environ with the interpreter's folder first on PATH, `extra`
    merged in, and for mutmut `no_proxy='*'` when no proxy variable is set."""
    env = dict(os.environ)
    folder = os.path.dirname(os.path.expanduser(str(python)))
    if folder:  # a bare name ("python") has no folder to put on PATH
        path = env.get("PATH", "")
        if path.split(os.pathsep)[0] != folder:
            env["PATH"] = os.pathsep.join(p for p in (folder, path) if p)
    env.update({k: str(v) for k, v in extra.items()})
    if mutmut and not any(env.get(name) for name in PROXY_VARS):
        env["no_proxy"] = "*"
    return env
