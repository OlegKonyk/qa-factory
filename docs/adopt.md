# Adopting the factory on a new application

A procedure for an agent (or a person) that sets the factory up against a Python application on
a fresh machine, from a fresh clone. Follow it in order; every step ends with a command and the
output it should give. Where it says "not verified", that part has not run anywhere yet.

Who this is for: a small Python service with a pytest suite, with or without browser tests.
The factory has run on two applications: linkding (Django, REST API, server-rendered pages with
Playwright tests), four tickets; and isso (a werkzeug comment server, API only, tests inside the
source package), one ticket shipped on 2026-10-13 (`docs/runs/2026-10-13-isso-no-cache-comment-views/`;
its mutation check could not run, section 7).
Everything below is written from those runs. The isso onboarding was done by an agent that read
only this guide; what it had to guess was folded back in (`docs/log.md`, 2026-10-13).

Pointing the factory at a work repository is Oleg's call, not a session's (`CLAUDE.md`, boundary).

## 1. What is ready

| Piece | State | Evidence |
|---|---|---|
| A ticket run through Frame, Plan, Implement, Verify, Review, Ship on one machine | built, measured | five runs shipped, `docs/runs/` |
| Tests written by a fresh headless session, after the change or blind from the ticket | built, measured | `docs/exploration.md`, track 1 |
| The revert check: every new test passes with the change and fails without it on an assertion | built, measured | `factory/checks/revert.py`; every run's `revert.json` |
| Mutation testing on the changed functions (mutmut 3.8.0), generated tests alone, with the developers' tests, developers' alone | built, measured | `factory/checks/mutants.py` |
| Lint of generated tests: ruff, no assertion, sleeps, mocks of the app's own code | built, measured | `factory/checks/lint.py` |
| The application's own suite with the new tests | built, measured | `factory/checks/suite.py` |
| One readable test case per test, linted | built, measured | `factory/checks/cases.py` |
| A repair round, then a stronger model's decision, then a person; caps per ticket | built, measured once (bundles ticket, 2026-10-10) | `docs/log.md` |
| Review by a fresh session; a fix round on request-changes | built, measured | `factory/steps/review.py` |
| Ship: a commit on `qa/<ticket id>` in the local worktree, the suite green | built, measured | `factory/steps/ship.py` |
| Resume after a crash, a run you can watch (Restate) | built, measured, optional | `docs/exploration.md`, track 2 |
| An application with no Python browser tests (API only) | built 2026-10-13, measured on isso (one ticket shipped) | `tests/test_verify_step.py`, the isso run |
| A helper file not named `helpers.py` (`test_helpers`) | built 2026-10-13, measured on isso | `targets/isso/app.json` |
| Mutation on decorated functions or code in `__init__.py` | not built: recorded as not applicable | section 7 |
| The same tests run against a deployed environment | not built | track 3, `docs/next-session.md` |
| Tests run against mocked dependencies, then the deployed run | not built; nothing decided | `docs/inputs.md` 2026-10-13 |
| A pull request to the application's repository instead of a local commit | not built | `docs/architecture.md`, point F |
| The factory writing the change itself (an agent-written Implement) | not built | the ticket points at a finished commit |
| Approval on a pull request; notifications | not built | approval is a file in the run folder |
| A `src/` layout for the source package | not verified | section 4, `source_package` |
| Anything not Python: the checks read pytest tracebacks and run mutmut | not built | |

Model spend per ticket on linkding, measured: 5.4 to 5.6 USD and 13 to 20 minutes when every check
passes in round 1; 8.5 USD when a repair round and the stronger model ran. Caps default to 15 USD
and three writer rounds per ticket.

## 2. The machine

Checked on macOS (Darwin 25.6, this laptop). Linux is expected to work; the cloud session that
built track 2 ran the factory's own tests on Ubuntu 24.04 (`docs/log.md`, 2026-10-12).

| Need | Version used here | Check |
|---|---|---|
| git | any recent | `git --version` |
| uv (brings Python 3.13 for the factory) | 0.12.5 | `uv --version` |
| Claude Code, logged in or with an API key | 2.1.296 | `claude --version`; `claude auth status` |
| just (optional; `scripts/check.sh` is what it runs) | 1.x | `just --version` |
| Node and npm (only if the application has Playwright browser tests) | 22 | `node --version` |
| Restate server and CLI (optional, `--engine restate`) | 1.7.13 | `restate-server --version` |

The application's own environment needs, inside its virtual environment: pytest, ruff, mutmut
3.8.0, pytest-xdist if its suite uses `-n`, and playwright with Chromium installed if it has
browser tests. The fetch script (section 4) installs mutmut and whatever the application's own
dependency files do not install (ruff, for isso: its test extra has pytest only).

**The application's Python version.** Use one from the application's own CI matrix and check that
its C extensions build (isso's matrix is 3.10 to 3.14; its `misaka` extension built on 3.13 here).

**Billing.** Every model call is a headless `claude -p` run. With a claude.ai login it bills the
subscription; with `ANTHROPIC_API_KEY` set it bills that key (Anthropic's Help Center, read
2026-10-12: API credits cover `claude -p` run with an API key). On this laptop
`scripts/with-console-key.sh <command>` takes the key from the Keychain; elsewhere export the
variable before the `run` command. `claude auth status` says which one is active. Set this up
before section 6: its first command already makes two model calls.

```
git clone git@github.com:OlegKonyk/qa-factory.git && cd qa-factory
just setup          # wires the commit hook; harmless without the guard's term list
uv sync
just check          # expect: ok shell syntax, ok ruff, ok pytest: N passed, "check: green"
```

Tests that need the linkding clone or a Restate server skip when those are absent.

## 3. What the application must have

1. A git repository with the change under test as a commit (or a branch head) whose parent is the
   code before the change. Today Implement is the developers' real commit: the ticket names
   `base` and `head` and the factory checks both out as worktrees.
2. A pytest suite that is green at `head`, runnable from the repository root with one Python
   interpreter the factory can call by path.
3. One folder for API tests (tests that call the service through its HTTP surface or its test
   client) with a helper file the writer reads for conventions (`helpers.py` by default; name
   another with `test_helpers` in the recipe). Optional: one folder of Python browser tests with a
   file-name pattern of their own, and its `helpers.py` (that name is fixed for browser tests).
4. A source package directory at the repository root (`mypackage/`, flat layout). Mutation testing
   mutates `source_package/<path>.py` and imports it as `source_package.path`; a `src/` layout is
   not verified. Tests inside the source package (isso's `isso/tests/`) are copied into the
   mutated tree with the rest; whether mutmut then finds them is not verified (on isso no mutant
   ran, section 7).
5. ruff configured (or default); pytest able to run one file at a time with the arguments in the
   recipe.
6. A strategy rule (section 4) saying where tests go.
7. **If the package must be installed to import** (a setuptools or similar project rather than a
   plain folder), install it editable from the clone, and check that the worktrees import their
   own code: in a worktree, `python -c 'import pkg; print(pkg.__file__)'` must print the
   worktree's path, not the clone's. Run the application's code only through `python -m ...` from
   the worktree (a script's own folder goes first on the path, so a probe script run from a
   worktree can silently import the clone). isso's `fetch.py` makes this check a step.

If the service calls other services, its suite must already run with those mocked or stubbed in
its own way; the factory runs the suite as it is and adds nothing.

## 4. The recipe: `targets/<app>/`

Copy `targets/linkding/` (browser tests) or `targets/isso/` (API only, a setuptools project) and
change every field. Three files and a `tickets/` folder.

**`app.json`**, read by every step. Paths may start with `~`. Required unless marked optional;
the steps index the required keys directly and fail with a `KeyError` on a missing one.

| Field | Meaning | Read by |
|---|---|---|
| `name` | the application's name; ticket ids start with `<name>-` | Verify (the test file slug) |
| `repo` | the clone the worktrees come from | fetch, Implement |
| `worktrees` | folder holding `<ticket id>/base` and `<ticket id>/head` | driver, fetch |
| `python` | the interpreter of the application's environment, absolute | every check |
| `source_package` | the package directory, relative to the repo root | mutation, lint (mocks of own code) |
| `pytest_args` | arguments for every pytest call, e.g. `["-p", "no:cacheprovider"]` | revert, suite, Ship |
| `api_tests_dir` | the API tests folder; the writer adds `test_<slug>_api.py` there | Verify, Implement, Ship |
| `test_helpers` (optional) | the helper file the writer reads first; default `<api_tests_dir>/helpers.py` | the writer prompt |
| `browser_tests_dir`, `browser_test_files` (optional, together) | the browser tests folder and its file pattern (`e2e_test_*.py`); omit both for an API-only application | Verify, Implement, Ship, revert |
| `test_support` | helper files the revert check puts back to their old version; `[]` if none | revert |
| `exclude_copy` | folders not copied when a tree is copied (`.git`, `node_modules`, `.venv`, `mutants`...) | revert, mutation |
| `mutmut.pytest_add_cli_args` | pytest arguments mutmut passes (`-p no:cacheprovider` at least; `-o django_find_project=false` for Django) | mutation |
| `mutmut.pre_create_dirs` | folders the application needs to exist inside the mutated copy; `[]` if none | mutation, Implement |
| `suite` | list of pytest invocations that make up the suite; the first is the API/unit suite, run again by Ship | suite check, Ship |
| `strategy` | the strategy rule's path, relative to the factory root | the writer prompt |
| `caps` (optional) | `{"writer_rounds": 3, "advice": 2, "usd": 15.0}` overrides | Verify, Review |

**`suite` from the application's own test command.** Take the arguments after `pytest` as they are
(isso: `make test` runs `pytest --doctest-modules isso/`, so `[["--doctest-modules", "isso"]]`).
`python -m pytest` from the repository root replaces a `PYTHONPATH=.`. Environment variables the
command sets (isso's `PYTHONHASHSEED=random`) have no place in the recipe and are dropped; say so
in the strategy rule if it matters.

**`strategy.md`**: the rule the test writer follows, in the application's own words: which folder
and base class or fixture for API tests, which for browser tests (or that there are none), what
the helper file is called and what it provides, that the application's conventions win, that
tests use the public surface and never the code's constants, that a test must fail on the old
code for a behavioural reason, how to run one file. `targets/linkding/strategy.md` and
`targets/isso/strategy.md` are the models. Keep it under a page.

**`fetch.py`**: a standard-library script that is safe to run twice. It must leave behind:

1. the clone at `repo`, on a known commit: a release tag when one is newer than the tickets'
   commits, otherwise a pinned commit (isso's newest tag was older than every 2026 candidate);
2. the environment at `python` with the application's dependencies, ruff and `mutmut==3.8.0`.
   For a uv project: `uv sync --python 3.13` in the clone, then `uv pip install --python <python>
   mutmut==3.8.0`. For any other project: `uv venv --python 3.13 .venv` in the clone, then
   `uv pip install --python .venv/bin/python -e '.[test]' ruff mutmut==3.8.0` (the extra's name
   is the application's);
3. with `--ticket <ticket.json>`: two worktrees, `<worktrees>/<ticket id>/base` at the ticket's
   `base` commit and `.../head` at its `head`, detached; for an installed package, the check of
   section 3, item 7 on each;
4. with `--prepare-e2e` (only with browser tests): the built assets and the browser installed in
   the head worktree.

It prints `ok    <step>` or `FAIL  <step>  <reason>` per step and exits 1 on any failure.

**A private recipe outside this repository.** A recipe for a repository that must not be named
here (`CLAUDE.md`, boundary) lives anywhere else, for example `~/factory-private/<app>/`. The
ticket's `app` and the recipe's `strategy` may be absolute paths; `python -m factory run` takes
`--runs-root <folder>` for the run folders. Nothing in this repository then refers to it.

## 5. The ticket: `targets/<app>/tickets/<slug>.json`

The model is `targets/linkding/tickets/bundle-filters-blind-2.json` (blind, with a contract).

```json
{
  "id": "<name>-<slug>",
  "app": "targets/<app>/app.json",
  "base": "<sha of the code before the change>",
  "head": "<sha of the change>",
  "qa_mode": "blind",
  "caps": {"usd": 8.0},
  "source": "where the ticket came from, for the record",
  "title": "one line",
  "description": "what changes and why, in plain words",
  "contract": ["the public surface, exactly: routes, fields, values, labels, status codes"],
  "acceptance_criteria": ["one observable outcome per line"]
}
```

- **Choosing the commit.** Its test changes must all sit under `api_tests_dir` (or the browser
  folder): Implement counts every other changed path as source, including tests in another
  language, snapshots, a changelog and configuration files. A changelog or a config file in
  `changed_source.json` is expected and harmless (mutation looks only at `.py` files under the
  source package, and skips every `__init__.py` and `migrations/`); a JavaScript test file there
  means the commit is a poor fit. Look at the changed functions before writing the ticket: prefer
  logic in plain functions outside `__init__.py`. mutmut 3.8.0 makes no mutant for most decorated
  functions, nor for a decorator that defines an inner function (measured on isso 7e91d59: none
  for its three changed functions), and code in `__init__.py` is skipped by the factory, so such a
  change gets no mutation verdict (section 7).
- `qa_mode`: `"blind"` writes the tests from the ticket and the code before the change, without
  seeing the change; omit it to write them after the change with the diff in view. Blind is the
  stronger proof and needs the contract stated; track 1 measured no mismatch on two tickets whose
  contract was written from the finished commits.
- `contract` is what the blind writer builds on. A ticket that does not state the public surface
  gives the blind lane nothing to hold to; write it, or run without `qa_mode`. Check it against
  both commits before the run (isso's was checked with a probe through the test client on `base`
  and `head`).
- `gate`: `"person"` parks the run after Verify until an answer file arrives. Leave it out, as
  above, and passing work is approved by the factory (decision of 2026-10-10).
- `caps.usd` is the hard model-spend cap of Verify and Review together.
- `area` (optional) names the folder of the readable cases; defaults to `source_package`.

## 6. Run it

```
uv run python targets/<app>/fetch.py --ticket targets/<app>/tickets/<slug>.json [--prepare-e2e]
uv run python -m factory run targets/<app>/tickets/<slug>.json --until implement
```

The second command runs Frame and Plan, one headless model call each (together about 0.33 USD and
30 s, measured on isso with Sonnet), then Implement, which calls no model. It must end with
`implement` passed and `.artifacts/runs/<ticket id>/implement/changed_source.json` listing the
changed source files, none of them under the test folders. If a Python test file is listed as
source, the recipe's test folders are wrong.

Then the whole ticket:

```
uv run python -m factory run targets/<app>/tickets/<slug>.json        # or under scripts/with-console-key.sh
uv run python -m factory status .artifacts/runs/<ticket id>
uv run python -m factory report .artifacts/runs/<ticket id>            # the QA evidence page
uv run python -m factory summary .artifacts/runs/<ticket id> > summary.md   # the numbers
```

- A run that stops for a person writes `question.md` in the run folder and exits 2. Put
  `answer.json` beside it (`{"decision": "approve", "by": "<who>", "note": "..."}` for a gate, or
  the escalation answers in `docs/decisions.md`, 2026-10-10) and run the same command again.
- A re-run skips passed steps and runs failed ones again. Caps live in `rounds.json` in the run
  folder and survive re-runs.
- Ship commits the tests and the readable cases on `qa/<ticket id>` in the head worktree and runs
  the suite there. Nothing is pushed.
- With Restate (optional): `restate-server --base-dir <data dir> &`, `uv run python -m factory
  restate serve &`, `uv run python -m factory restate register`, then `run ... --engine restate`;
  the service runs the steps, so start it under the key script, not the `run` command.

## 7. Reading the verdicts

`python -m factory report <run folder>` puts all of this on one page.

- **Revert check** (`verify/revert.json`), per test: `proves-behaviour` (fails on the old code on
  an assertion: the test proves the change), `passes-without-change` (allowed; a regression
  guard, which the report prints as "passes on the old code too: proves nothing"), `missing-name` (fails on the old code only because a name does not exist
  yet: the test proves the code is new, not what it does; fails the check), `crash`,
  `head-fails` (fails with the change; fails the check).
- **Mutation** (`verify/mutation.json`): mutants checked and killed on the changed functions, in
  all and on the changed lines, for the generated tests alone, with the developers' tests, and
  the developers' alone. Scores are reported, not thresholded; the check fails only when mutmut
  could not run, no mutant was checked, or the generated tests kill no mutant on the changed lines.
- **The developers' own tests** (`verify/developers_revert.json`): the same revert check on the
  tests the change itself added, reported with the same verdicts and never a failure. It answers,
  per ticket, whether the tests written with the code prove the behaviour. On a finished run,
  `python -m factory devtests <run folder>` runs it alone, with no model call.
- **Mutation not applicable**: when mutmut makes no mutant for any changed function (decorated
  functions, section 5), the report says so under `skipped` and the run goes on; the revert check
  is then the only proof the tests exercise the change. This is not a test failure; do not retry.
- **Lint**, **suite**, **cases**: pass or the findings.
- `rounds.json`: every model call, its cost and round; `verify/escalation-<k>.json`: the stronger
  model's decision when one was asked.

## 8. The onboarding checklist

An agent onboarding an application reports these, each with the command and its output:

1. `just check` green on the factory.
2. `fetch.py` ends with every step `ok`, twice (the second run changes nothing).
3. `run --until implement` passes, and `changed_source.json` holds no Python test file.
4. The whole ticket runs; Verify's checks pass or the run says which did not and why.
5. `report.md` for the run, copied with `summary.md` and the generated tests into
   `docs/runs/<date>-<ticket id>/`.
6. Every place this guide was wrong or silent, as a list, folded back into this file.

## 9. What is not covered

The factory has not run on a bug-fix ticket, on a service with external dependencies, on a `src/`
layout, on Windows, on more than one ticket at a time, or against a deployed environment. Each is
a run away, not a design away; the first run of each will find what this guide does not say.
