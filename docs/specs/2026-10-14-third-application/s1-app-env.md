# s1 · The application's environment in every check: PATH, and mutmut's fork on macOS

Branch `fix/app-env`, worktree `~/dev/qa-factory-wt/appenv`. Written 2026-10-14 after the scouting
of roadmap item 3's application (gafaelfawr, FastAPI under `src/`, Postgres and Redis through
testcontainers). Two facts measured there by an Opus scout, both generic:

1. **The venv's bin folder is not on PATH.** Three of its tests run `alembic` as a subprocess and
   fail with `FileNotFoundError: 'alembic'` under plain pytest; `nox` puts `.venv/bin` first on
   PATH, the factory's subprocesses inherit `os.environ` unchanged. Any application whose tests
   spawn a console script from its environment (`alembic`, `celery`, its own CLI) fails the same
   way in the revert check, the suite check and Ship.
2. **mutmut 3.8.0 on macOS: every mutant child segfaults (exit -11)** in
   `_scproxy.get_proxy_settings` (urllib's macOS proxy lookup, not fork-safe) unless some `*_proxy`
   variable is set; `no_proxy='*'` makes urllib skip the lookup. Measured: 62 of 62 mutants -11
   without it, 62 of 62 run (49 killed, 13 survived) with it. Any application that imports
   `requests` or `urllib.request` at import time hits it.

## The change

Add `factory/checks/appenv.py` with one function:

```python
def app_env(python, *, mutmut=False, **extra) -> dict[str, str]:
    """The environment for a subprocess that runs the application's interpreter or a tool from
    its environment: a copy of os.environ with the interpreter's folder first on PATH, `extra`
    merged in, and for mutmut `no_proxy='*'` when no proxy variable is set."""
```

- PATH: `os.path.dirname(python)` prepended with `os.pathsep`, once (not duplicated when it is
  already first). `python` may start with `~` elsewhere, but by the time the checks run it is the
  absolute path from the recipe (`app["python"]`); expand `~` anyway with `os.path.expanduser`.
- `mutmut=True`: if none of `no_proxy`, `NO_PROXY`, `http_proxy`, `HTTP_PROXY`, `https_proxy`,
  `HTTPS_PROXY`, `all_proxy`, `ALL_PROXY` is set, set `no_proxy = "*"`. Not only on macOS: it is
  harmless elsewhere and keeps one code path.
- `extra` keys override (revert's `PYTHONPATH` and the failsort output variable come through it).

Use it in **every** subprocess that runs the recipe's `python`, `mutmut` beside it, or `ruff`
beside it: grep `subprocess.run(` and `subprocess.Popen(` across `factory/checks/` and
`factory/steps/` and change each such call (git calls are not touched): `revert.py` (`_env`
becomes a thin call), `suite.py`, `lint.py`, `cases.py` if it runs pytest or ruff, `mutants.py`
`_invoke` (with `mutmut=True`), `ship.py` (the suite after the commit), `devtests.py` and
`mutation_rerun.py` if they spawn anything themselves rather than through the checks, and the
e2e/browser path in `revert.py` or wherever Playwright tests are run. Read each call; where a call
already builds an env, merge rather than replace.

## Tests (`py-testing` conventions, in `tests/`)

- `tests/test_appenv.py`: PATH starts with the interpreter's folder; an existing PATH is kept after
  it; calling it on a PATH that already starts with that folder does not duplicate it; `extra`
  wins; `mutmut=True` sets `no_proxy='*'` when nothing proxy-like is set and leaves it alone when
  `HTTP_PROXY` (or `no_proxy`) is set (use `monkeypatch.setenv`/`delenv`).
- One test per changed call site is too much; instead one test that drives a real subprocess
  through the suite check (or the revert check, whichever has the simpler existing test harness,
  read `tests/test_suite_check.py` / `tests/test_revert*.py`) with a fake interpreter folder that
  holds an executable `probe` script, and a tiny pytest file that asserts `shutil.which("probe")`
  is not None. That proves the bin folder reaches the test process. Use `sys.executable` as the
  interpreter and symlink or copy it into the temporary folder beside `probe`.
- `mutants._invoke` is already tested through a fake `subprocess.run` seam
  (`tests/test_mutants.py`, `test_run_mutates_an_undecorated_copy...`): extend or add a case that
  asserts the env passed has `no_proxy == "*"` and PATH starting with the interpreter's folder.

## Docs, same branch

- `docs/adopt.md`:
  - section 2 ("The machine"): a sentence that every check runs with the application
    environment's bin folder first on PATH (tests may spawn `alembic` or another console script),
    and that mutmut's children get `no_proxy='*'` when no proxy variable is set (the macOS fork
    crash, measured 2026-10-14 on gafaelfawr; harmless elsewhere). On this machine only: Docker
    runs through Colima, `docker compose` (the plugin) is absent and `docker-compose` 5.5.0 is the
    binary; testcontainers needs `TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock`
    exported before the run, else every container start fails with a mount error on
    `~/.colima/default/docker.sock` (measured). Put the machine-only lines in a short "This
    machine only" paragraph so another machine's reader can skip it.
  - section 3 item 7: for a `src/` layout the editable install's `.pth` points at the clone, so a
    worktree imports the clone's code unless pytest puts the worktree's `src` first: add
    `"-o", "pythonpath=src"` to `pytest_args` (two list items; one item `"-o pythonpath=src"` is
    silently ignored, measured), with every source root space-separated when there are several
    (`"pythonpath=src client/src"`), and never in `mutmut.pytest_add_cli_args` (pytest would put
    the copy's unmutated `src` ahead of `mutants/src`; mutmut puts `mutants/src` on the path
    itself). The item-7 check for that layout: run a one-line test through pytest in the worktree
    with those arguments and print the module's `__file__`, or `PYTHONPATH=src python -c ...`.
    Keep the flat-layout wording as it is.
  - section 4, the `pytest_args` row: mention `-o pythonpath=src` for a `src/` layout and that
    `mutmut.pytest_add_cli_args` must not carry it.
  - section 5 or 6, wherever base and head environments are discussed (search "interpreter"): one
    interpreter serves base and head, so a fix older than the environment's dependency pins may
    not import or may fail its suite at head's environment; prefer a fix from the last months
    (measured on gafaelfawr: a May fix was red and a March fix did not import under October's
    environment).
- `docs/log.md`: an entry under today's date with the two facts, their numbers, and that the
  factory tests are the only measurement so far.

## Definition of done

`just check` green in the worktree, output pasted; `ruff check` and `ruff format --check` clean.
No git commands.
