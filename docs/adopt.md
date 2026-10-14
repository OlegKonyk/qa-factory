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
| Mutation on decorated functions or code in `__init__.py` | built 2026-10-14, measured on isso; a decorator whose body is a decorated inner function still gets none | section 7 |
| The same cases run against a deployed instance, data through the public API | built 2026-10-14, measured on linkding from its Docker image (4 of 4 cases); a session writes the thin suite, not a step | section 10, `docs/exploration.md` track 3 |
| Tests run against mocked dependencies, then the deployed run | not built; nothing decided | `docs/inputs.md` 2026-10-13 |
| A pull request to the application's repository instead of a local commit | not built | `docs/architecture.md`, point F |
| The factory writing the change itself (an agent-written Implement) | not built | the ticket points at a finished commit |
| A gate at every step: stop, tell, list, answer, correct | built 2026-10-14, proved on one ticket through Plan | section 6, `docs/runs/2026-10-14-linkding-sort-by-modified-vague/` |
| Approval on a pull request | not built | approval is a file in the run folder |
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

Before the recipe, score the application against the twelve-item checklist in
`docs/exploration.md` ("What makes a repository agent-friendly for this loop") and record what it
lacks in the onboarding report; fix only what the run needs. Read the application's own agent
file (`AGENTS.md`, `CLAUDE.md`) first; write one if there is none, with the commands this guide
needed.

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
   mutated tree with the rest, and mutmut runs them there (measured on isso 7e91d59, 2026-10-14).
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
| `gates` (optional) | where a run stops for a person, per step: `{"verify": "person"}`. `auto`: the step stops only when its own rule says so; `model`: a stronger model decides before a person (Verify only; elsewhere the same as `auto` for now); `person`: the step always stops at its end. Default `verify: model`, every other step `auto`; the ticket's `gates` win | Frame, Plan, Verify, Review, Ship, `python -m factory waiting` |
| `approver` (optional) | the name a question is addressed to; default `Oleg` | Verify |
| `notify_url` (optional) | a URL that gets a JSON POST when a run stops for a person (section 6); the ticket's wins | driver |

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
  source package, `__init__.py` included, and skips `migrations/`); a JavaScript test file there
  means the commit is a poor fit. Look at the changed functions before writing the ticket.
  mutmut 3.8.0 ignores decorated functions, so in the copy it mutates the factory turns each
  decorator of a top-level function or method into a comment and applies it at the end of the
  module instead (`f = dec(f)`); line numbers do not move. Left decorated, and so without a
  mutant: `@staticmethod` or `@classmethod` stacked with another decorator (alone, mutmut
  handles them), `@property` and its setters, a name defined twice (`@overload`), and functions
  nested in functions. A decorator that defines a decorated inner function (`@wraps(func) def
  wrapper`) gets no mutant (measured on isso 7e91d59). A change that only adds a decorator line
  gets mutants in the function's body but none on a changed line. A change made only of
  functions without a mutant gets no mutation verdict (section 7).
- `qa_mode`: `"blind"` writes the tests from the ticket and the code before the change, without
  seeing the change; omit it to write them after the change with the diff in view. Blind is the
  stronger proof and needs the contract stated; track 1 measured no mismatch on two tickets whose
  contract was written from the finished commits.
- `contract` is what the blind writer builds on. A ticket that does not state the public surface
  gives the blind lane nothing to hold to; write it, or run without `qa_mode`. Check it against
  both commits before the run (isso's was checked with a probe through the test client on `base`
  and `head`).
- `gates` (optional): the same per-step modes as the recipe's (section 4), and they win over it:
  any of `frame`, `plan`, `verify`, `review`, `ship`. `{"verify": "person"}` parks the run after
  Verify until an answer file arrives; `{"frame": "person", "plan": "person", "review": "person",
  "ship": "person"}` stops at each of those too. Leave it out, as above, and the run stops only
  where a step's own rule says so (section 6) and passing work is approved by the factory
  (decision of 2026-10-10). The older single field `"gate": "person"` is still accepted and means
  `{"verify": "person"}`.
- `description`, `contract` and `acceptance_criteria` are what Frame checks: when a criterion is
  not testable, or the ticket and the old code leave out a fact a test writer needs (a route, a
  field name, a value, a label, a status code), Frame stops and asks. A person's answer may replace
  these three fields for the run (section 6, the clarified ticket); the ticket file is not changed.
- `notify_url` (optional): overrides the recipe's for this ticket.
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

- A run that stops for a person writes `question.md` in the run folder and exits 2. The question
  names its kind, who is asked, the accepted answers with what each means, and an example. Put
  `answer.json` beside it (`{"decision": "approve", "by": "<who>", "note": "..."}` for an approval;
  `retry` with `guidance`, `recheck` with `round`, `change_is_wrong`, `environment` or `fail` for
  Verify's escalation, `docs/decisions.md`, 2026-10-10) and run the same command again. `by` is
  required: an answer without it, or with a decision the question does not accept, is left in
  place and the run prints `answer: <what is wrong>` and exits 2 again. The old approval form
  `{"approved": true, "by": "<who>"}` still works. The consumed answer is kept as
  `steps/NN-<step>.answerM.json` with the time it was read (`answered_at`), and the question it
  answered as `steps/NN-<step>.roundK.json`, so a step that stops twice keeps both; `status` names who
  answered on the step's line and the report has a section "Who answered".
- `uv run python -m factory waiting [--runs-root <folder>] [--json]` lists every run that waits for
  a person, one line each: ticket, step, kind, who, since when, the question's start and its path.
  A run whose answer is written but not yet read says "answer pending", or "answer refused: <what
  is wrong>" when the run would refuse it; none prints "nothing is waiting".
- When a run stops for a person it tells, best effort: on macOS with `osascript` on the PATH a
  desktop notification (this machine only; nothing elsewhere), and with `notify_url` set a JSON
  POST (`ticket`, `step`, `kind`, `who`, `question`, `run_dir`, `question_path`, 5 s timeout). A
  failure to tell prints one `notify:` line and never stops the run. On a headless machine or in a
  CI job set `QA_FACTORY_NO_NOTIFY=1` and it tells nobody.
- Where each step stops under `auto` (the default everywhere but Verify), and the answers it
  accepts. Under `person` each stops (Ship before its commit). The answer names one `decision`;
  "carries" is the extra field that answer may hold.

  | Step | Stops under `auto` when | Answers (what each carries) |
  |---|---|---|
  | Frame (`clarify`) | a criterion has `testable: false`, or `missing_contract` is not empty; ambiguities alone never stop it | `proceed` (go on with the frame as read), `clarify` (carries `ticket`: any of `description`, `contract`, `acceptance_criteria`; Frame runs again on the clarified ticket and its rule applies again), `decline` |
  | Plan (`plan`) | the plan says `risk: "high"`, or lists `unknown_patterns` (patterns the strategy does not cover) | `approve`, `edit` (carries `plan`: a path to a JSON file in the plan's structured shape, or to `plan/plan.json` itself after editing it in place, relative to the run folder or absolute, or the object inline; the file the answer replaces is kept as `plan/plan.before-edit.json`, which for an in-place edit is already the edited one, so copy the original first if it matters), `decline` |
  | Verify (`approval`, `escalation`) | the stronger model cannot decide a failure (mode `model`, the default) | `approve`/`decline`; `retry` (carries `guidance`), `recheck` (carries `round`), `change_is_wrong` |
  | Review (`review`) | the review still requests changes after its fix round, or no writer round is left for one | `sign_off` (carries `note`, kept in the reason), `another_round` (one more fix round when a writer round is left, else the step fails), `decline`; under `person` an approving review asks `sign_off` or `decline` |
  | Ship (`ship`) | never; under `person` it stops before the commit | `approve` (commit and run the suite), `decline` |

- **The clarified ticket.** Frame's `clarify` answer writes its fields to
  `<run folder>/ticket.clarified.json`. From then on every step, in this run and every re-run,
  gets the ticket file with those fields replaced (only `description`, `contract` and
  `acceptance_criteria`; any other key there is an error), and `ticket.json` in the run folder
  records the merged ticket. Everything else, `caps` included, still comes from the ticket file.
- **Editing a passed step's output by hand.** Edit the file (for example `plan/plan.json`), then
  `uv run python -m factory redo <run folder> <step> --by <who> [--note "..."] [--rerun]`. Every
  later step's record becomes an earlier round (`steps/NN-<step>.roundK.json`), so the next `run`
  resumes after the edited step; `--rerun` archives the step's own record too, so it runs again.
  It writes `steps/NN-<step>.redoK.json` (who, when, the note, and the sha256 of the step's
  artifact files before, as the step's record kept them when it passed, and after, as found when
  `redo` runs; `unknown` for a missing file or a record from before records kept hashes) and prints
  what it archived. It refuses a step that has not passed and a run waiting at a gate, and says what to
  do instead.
- A re-run skips passed steps and runs failed ones again. The spend so far lives in `rounds.json`
  in the run folder and survives re-runs; the caps are read from the ticket (`caps`) on every run.
- A Verify stopped at its spend cap after every check passed (the report says `"resumable": true`
  and `stopped_at`) resumes on re-run at the readable test cases, with the same tests and no new
  writer round. To continue, raise `caps.usd` in the ticket file and run the same command again.
  A cap hit in a writer round or a stronger-model call starts a fresh writer round on re-run.
- Ship commits the tests and the readable cases on `qa/<ticket id>` in the head worktree and runs
  the suite there. Nothing is pushed. Under `gates.ship: person` it asks first and writes nothing
  to the worktree until approved.
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
  tests the change itself added or modified, reported with the same verdicts, each test labelled
  new or modified, and never a failure. It answers, per ticket, whether the tests written with the
  code prove the behaviour. On a finished run, `python -m factory devtests <run folder>` runs it
  alone, with no model call.
- **Mutation not applicable**: when mutmut makes no mutant for any changed function (the shapes
  in section 5), the report says so under `skipped` and the run goes on; the revert check is then
  the only proof the tests exercise the change. This is not a test failure; do not retry. A
  changed function that alone got no mutant is listed in each run's `unmutated`; a decorated
  function the rewrite left alone, with its reason, in `left_decorated`; and when the rewritten
  copy broke mutmut's run and the plain copy was used instead, the run says so under
  `undecorate`. On a finished
  run, `python -m factory mutation <run folder>` runs the mutation check again with no model call
  (it puts the shipped tests back from `verify/tests/` if they are missing) and writes
  `verify/mutation-rerun.json`; exit 0 when mutmut ran or was skipped, 1 on an error.
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
layout, on Windows, or on more than one ticket at a time; against a deployed instance only one
feature of linkding has run (section 10). Each is
a run away, not a design away; the first run of each will find what this guide does not say.

## 10. The same cases against a deployed instance

The readable cases Verify writes are the artifact that crosses from the application's suite to a
deployed environment. `targets/linkding/deployed/` is the worked example: the four cases of the
sort feature as a thin pytest suite that takes a base URL and a token from the environment and
creates every bookmark through the REST API (its README has the container recipe, the variables,
the command and what had to change from the in-suite tests). It needs the `deployed` dependency
group (`uv sync --group deployed`, then `uv run --no-sync playwright install chromium`) and is
run by path; the root `uv run pytest` does not collect it. For another application, write the
same shape beside its recipe: one test per case, data through the public API only, every list
request scoped by a marker unique to the test, cleanup in a `finally`. Writing that suite is
still a session's work, not a factory step (`docs/roadmap.md`).
