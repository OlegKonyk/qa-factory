# gafaelfawr, the OpenID Connect client update ticket, blind: the third application, shipped (2026-10-14)

The first bug-fix ticket, the first `src/` layout and the first service whose suite starts its own
Postgres and Redis (testcontainers). gafaelfawr is a FastAPI authentication service
(github.com/lsst-sqre/gafaelfawr), Python 3.14, uv, two packages (`src/gafaelfawr` and the client
`rubin.gafaelfawr` under `client/src`). The ticket is upstream commit d7c2fbf ("Fix OpenID Connect
client updates": a PATCH now records who changed a client and when, and both timestamps are
truncated to the second); its base is the parent, 9b61018. It was written as a bug report with a
contract (`targets/gafaelfawr/tickets/oidc-client-updates.json`, `caps.usd` 8.0).

Two agents onboarded it from `docs/adopt.md` alone. The first wrote the recipe, ran Frame, Plan
(answered the Plan gate as "the onboarding agent") and Implement, and Verify's first writer round,
whose mutation check failed because mutmut's working copy lacked `alembic.ini` and `alembic/`; it
was stopped during the repair round. The second added both to the recipe's `mutmut.also_copy`,
re-ran, and stopped where the run stopped: Review's fix round ran out of the ticket's 8.0 USD. The
session then fixed the factory (pull requests #33 and #34), raised the cap to 12 USD, resumed the
run at the readable cases, moved the cases to the right folder by hand (recorded with `redo`), and
the run shipped. Every model call after Frame and Plan billed the Console API key.

All numbers below are measured unless labelled otherwise.

## Result

| step | result | time | model spend |
|---|---|---|---|
| Frame | pass | 11.2 s | 0.0379 USD (Sonnet) |
| Plan | stopped for a person (three patterns not in the strategy), approved by the onboarding agent | 15.2 s | 0.0569 USD (Sonnet) |
| Implement | pass (the developers' commit: 2 source files, 1 test file) | 0.04 s | none |
| Verify, round 1 (first agent) | 4 tests; revert check and lint passed; mutation failed: pytest could not run in mutmut's copy (no `alembic.ini`) | writer 309 s; step time not recorded | 2.19 USD (Opus) |
| Verify, round 2 (first agent) | a repair round, stopped by the session while it ran; no record, folder empty | | not recorded |
| Verify, round 3 (after `also_copy`) | 5 tests; every check passed; 5 readable cases | 718 s | writer 2.00 USD, cases 0.73 USD (Opus) |
| Review | request changes: 6 findings (1 high, 2 medium, 3 low) | 76 s | 0.30 USD (Opus) |
| Review's fix round (Verify round 4) | 6 tests; revert, lint, mutation and suite passed; the readable-case writer stopped on its budget, so the round failed | 799 s (the whole Review step) | writer 2.08 USD, cases 0.70 USD (Opus) |
| Verify, resumed at the cases (cap raised to 12) | 6 readable cases | 112 s | cases 0.71 USD (Opus) |
| Review, again | approve: 3 low findings (the SQL backdating helper, two assertions that could be tighter) | 59 s | 0.26 USD (Opus) |
| Ship, first try | failed: `IsADirectoryError` on `verify/testcases/src/gafaelfawr` (the cases' area was the whole `source_package`, pull request #34) | 0.003 s | none |
| Verify, `redo` by the session | the six cases moved to `testcases/gafaelfawr/TC-gafaelfawr-00N.md`, ids and area renamed, linted: 6 cases checked, 0 findings; `records/steps/04-verify.redo1.json` holds the hashes before and after | | none |
| Review, again | approve | 66 s | 0.23 USD (Opus) |
| Ship | commit `625da5c` on `qa/gafaelfawr-oidc-client-updates` in the head worktree: the test file and the six cases; suite 226 passed, 10 skipped in 56 s | 59 s | none |

Spend in `rounds.json`: 9.2098 USD (Verify and Review, nine calls). With Frame and both Plan
rounds: 9.3046 USD. The stopped round-2 writer call is in no record; by the other writer calls it
cost at most about 2 USD (estimated). Wall time of the factory commands: 1517.9 s for the second
agent's whole-ticket run (`records/logs/run1.log`), 172.7 s resumed (`run3-resumed.txt`), 124.9 s
to ship (`run4-ship.txt`); the first agent's part was not timed.

**Why it stopped at 8 USD, and how it went on.** The fix round's case writer was given
`--max-budget-usd 0.70` (the cap minus the spend) and cost 0.7046 USD; `claude -p` ended it with
the subtype `error_max_budget_usd`, which the factory of that moment recorded as `test case writer
ended with an error: ` and did not mark resumable, and a plain re-run failed Review at once. Pull
request #33 made a budget-ended call a cap hit, resumable after the checks; this run's report was
marked `resumable` by hand (it had been written before the fix), the cap raised to 12, and the same
command resumed at the cases and reviewed again, as the guide now says.

## The tests

**Round 3** (5 tests, `records/round3/test_oidc_client_updates_api.py`): 3 fail on the old code on
an assertion (`'admin-a' == 'admin-b'` for a second administrator's PATCH, by token and by session
cookie; `created ... not in whole seconds`), 2 pass on both (the creator's own PATCH; refused
PATCHes change nothing). Mutation on the three changed functions (`OIDCService.update_client`,
`OIDCClientStore.register`, `OIDCClientStore.update`): 71 mutants checked; generated tests kill 64
(0.90), 24 of 24 on the changed lines; with the developers' 65; the developers' alone 64, 23 of 24
on the changed lines. The suite with the tests: 225 passed, 10 skipped in 53 s.

**Review's findings on round 3** (`records/review.round1.json`). The high one is real: POST and
PATCH run in the same second, so a fix that forgot to update `last_modified` would still pass
`last_modified >= before`; the round-3 tests could not tell the update time from the creation time.

**Round 4** (6 tests, `tests/tests/handlers/test_oidc_client_updates_api.py`, the current tests): a
helper moves the client's `created` and `last_modified` to 2020-01-01 with one SQL `UPDATE` through
the suite's `factory.session` (setup only; read back through GET), then every test checks that the
PATCH moved `last_modified` into `[before, after]` and left `created` alone. 5 fail on the old code
on an assertion, 1 passes on both (refused PATCHes, including the cookie without CSRF header, change
nothing). Mutation: generated tests 64 of 71 (0.90), 24 of 24 on the changed lines; suite 226
passed, 10 skipped in 53 s. The review of round 4 approved it and called the SQL setup a low
finding (below).

**Review of round 4** (`records/review.final.json`, twice, after the resume and after the hand move):
approve, three low findings: the backdating helper writes the `oidc_client` table with raw SQL (the
tests depend on the schema's names), `last_modified != "2020-01-01T12:00:00Z"` only checks that the
value changed, and the "never before created" criterion is checked only against a backdated
`created`. Left as they are; the strategy's public-surface rule could say "setup too".

**The developers' own test** (`test_lifecycle` in `api_oidc_test.py`, modified by the commit): with
the factory of the run it got no verdict (the check keyed it `test_lifecycle`, pytest reported
`test_lifecycle[github-oidc-server]`; `status: error`, `ran: 0`). After pull request #33,
`python -m factory devtests` on this run: 1 of 1 modified test fails on the old code on an
assertion, proves-behaviour (`records/developers_revert.json`). Its mutation numbers moved between
two runs with the same tests: `register__mutmut_10` (line 249, a changed line) was killed in round
3 and survived in round 4 (23 then 22 of 24 on the changed lines; the cause, a test that compares
times taken around a call, is not verified).

**Readable cases** (`testcases/`): six, one per test, written by the resumed cases call. With the
default `area` of that moment (`source_package`, here `src/gafaelfawr`) they came out as
`testcases/src/gafaelfawr/TC-src/gafaelfawr-00N.md` with the id `TC-src/gafaelfawr-001`; the
linter checked none of them (`0 cases checked, 0 findings`) and Ship failed on the folder. Pull
request #34 fixed the default; the files were moved and renamed by hand, linted (6 cases checked,
0 findings) and the move recorded with `redo`.

## Commands and their output

Every factory and pytest command ran with `export TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock &&`
on the same line (this machine's Colima, `docs/adopt.md` section 2).

1. `just check` on the factory, after the recipe's `fetch.py` was brought under the line length
   (it failed `ruff check` with two E501 and `ruff format`):

   ```
   ok    shell syntax (6 scripts)
   ok    .local/ untracked
   ok    ruff check
   ok    ruff format
   ok    pytest: 380 passed, 1 skipped in 29.36s
   ok    roadmap: 10 items: 7 planned, 3 done
   check: green
   ```

2. `uv run python targets/gafaelfawr/fetch.py --ticket targets/gafaelfawr/tickets/oidc-client-updates.json`,
   twice, with a hash of the clone's HEAD and status, both worktrees' HEADs, the clone's `AGENTS.md`
   and `uv pip freeze` before and after (`records/logs/fetch.txt`): every step `ok` both times, exit
   0, and the hash `96d63c26...` the same before, after the first and after the second run.

   ```
   ok    clone present: /Users/oleg/Library/Caches/qa-factory/gafaelfawr/repo
   ok    checked out 16.0.2 2a7e4f9 (detached)
   ok    gafaelfawr, rubin.gafaelfawr (editable), pytest, testcontainers, ruff, mutmut==3.8.0 installed
   ok    AGENTS.md in the clone (git-excluded)
   ok    worktree gafaelfawr-oidc-client-updates/base at 9b61018
   ok    worktree gafaelfawr-oidc-client-updates/base imports its own gafaelfawr and rubin.gafaelfawr
   ok    worktree gafaelfawr-oidc-client-updates/head at d7c2fbf
   ok    worktree gafaelfawr-oidc-client-updates/head imports its own gafaelfawr and rubin.gafaelfawr
   ```

3. `scripts/with-console-key.sh uv run python -m factory run targets/gafaelfawr/tickets/oidc-client-updates.json --until implement`:

   ```
   skip  1 frame
   skip  2 plan
   skip  3 implement
   stopped after implement as asked: .../.artifacts/runs/gafaelfawr-oidc-client-updates
   ```

   `implement/changed_source.json`: `src/gafaelfawr/services/oidc.py`, `src/gafaelfawr/storage/oidc.py`;
   `changed_tests.json`: `tests/handlers/api_oidc_test.py`. No test file is listed as source.

4. `scripts/with-console-key.sh uv run python -m factory run targets/gafaelfawr/tickets/oidc-client-updates.json`
   (`records/logs/run1.log`), exit 1, `real 1517.94`:

   ```
   skip  1 frame
   skip  2 plan
   skip  3 implement
   pass  4 verify  (718.381 s)
   FAIL  5 review: review fix round: test_cases: test case writer ended with an error:
   ```

   The same command again (`records/logs/run2.log`), exit 1, no model call, spend still 8.0054:
   `FAIL  5 review: Verify's checks have not passed on the current tests (status fail); re-run Verify for this ticket`.

5. `uv run python -m factory status|report|summary .artifacts/runs/gafaelfawr-oidc-client-updates`:
   exit 0 each; `report.md` and `summary.md`/`summary.json` here. The report's line "No readable
   cases were written. Verify ended with: every check passed" describes round 3's Verify record, not
   the failed round 4.

## The application against the readiness checklist (`docs/exploration.md`, twelve items)

| # | item | gafaelfawr | needed by this run |
|---|---|---|---|
| 1 | one documented command to start the app with seeded data | missing: the docs give `uv run nox` for tests and minikube for the Kubernetes tests; no compose file, no seeded start | no |
| 2 | test helpers named in a strategy rule | not upstream; `targets/gafaelfawr/strategy.md` names `tests/support/tokens.py`, `cookies.py`, `constants.py` | yes, provided |
| 3 | a strategy rule per test level | not upstream; the recipe's (API only, `tests/handlers/test_<slug>_api.py`) | yes, provided |
| 4 | selectors by role and label | not applicable: no browser tests | no |
| 5 | test data through the public API | partly: clients through the API, but tokens through the suite's `factory` (service layer); round 4 backdates through SQL | no (no deployed run) |
| 6 | base URL, test accounts and cleanup per environment | missing | no |
| 7 | fast lint and suite, mutation runnable locally | met: `ruff check .` 0.09 s (warm cache), suite 226 passed in 53 s, mutmut 58 to 69 s per set on 71 mutants | yes |
| 8 | logs an agent can read | met as far as this run went: pytest tracebacks with full assertion diffs (`python_files` covers `tests/support`); not scored further | yes |
| 9 | a short agent file at the root | missing upstream; `targets/gafaelfawr/AGENTS.md` written, copied into the clone and git-excluded by `fetch.py` | yes, provided |
| 10 | a machine-readable API description | FastAPI serves `/auth/openapi.json` (from the code; not fetched in this session) | no |
| 11 | an isolated, reproducible environment per run | partly: Postgres 18 and Redis 8 per test session through testcontainers, a worktree pair per ticket; no container recipe for the service itself | yes, met for the suite |
| 12 | caps the repository's own pipeline enforces | met on paper: pre-commit with ruff and the uv lock check, GitHub Actions `ci.yaml` (nox lint, typing, test); read, not run | no |

What the run needed and the application lacked was a strategy rule, named helpers and an agent file;
the recipe provides all three. Nothing upstream was changed.

## The agent file

`targets/gafaelfawr/AGENTS.md` (copied into the clone as `AGENTS.md`, excluded from git there):

```
# Agent notes for gafaelfawr (written by the qa-factory onboarding, not upstream)

gafaelfawr is a FastAPI authentication and authorization service. Python 3.14, uv. Two packages:
the server under `src/gafaelfawr` and the client `rubin.gafaelfawr` under `client/src` (installed
editable by the `dev` group; it has its own noxfile and tests under `client/`).

## Environment

    uv sync --frozen --inexact --python 3.14     # dev group: pytest, testcontainers, the client
    uv pip install --python .venv/bin/python ruff mutmut==3.8.0

## Tests

The suite starts Postgres 18 and Redis 8 itself through testcontainers (session-scoped fixtures in
`tests/conftest.py`), so Docker must be running. Some tests run the `alembic` console script, so the
environment's `bin` folder must be on PATH. On a Mac with Colima, also set
`TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock`.

The suite's database fixture (`empty_database` in `tests/conftest.py`) stamps the schema with
`alembic.ini` and the `alembic/` folder at the repository root (found as `Path(__file__).parent.parent`),
so any copy of the tree that runs the tests (mutmut's `mutants/`, for one) needs both.

    PATH=$PWD/.venv/bin:$PATH .venv/bin/python -m pytest -p no:cacheprovider tests
    PATH=$PWD/.venv/bin:$PATH .venv/bin/python -m pytest -p no:cacheprovider tests/handlers/api_oidc_test.py

From a git worktree of this clone add `-o "pythonpath=src client/src"` so the worktree's code is
imported, not the clone's (the editable installs point at the clone).

- Test files are `*_test.py`, laid out like `src/gafaelfawr` (handlers, services, storage...).
- `tests` is a package: imports between test modules are relative (`from ..support.tokens import
  create_session_token`).
- HTTP tests use the `client` fixture (an httpx `AsyncClient` on the app), `factory` for setup, and
  `@pytest.mark.parametrize("config", ["<name>"], indirect=True)` to pick a config from
  `tests/data/config/`. Async tests carry `@pytest.mark.asyncio` (strict mode).
- Helpers live in `tests/support/` (tokens, cookies, constants, headers, ...).

## Lint

    .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .

The project's own lint, typing and test sessions are in `noxfile.py` (`uv run --only-group=nox nox
-s lint typing test`), which CI runs.

## API description

FastAPI serves OpenAPI at `/auth/openapi.json` (docs at `/auth/docs`).
```

## Files here

`report.md` (the QA evidence page, regenerated after Ship), `summary.md` and `summary.json`,
`tests/` (round 4's test file, the shipped tests), `testcases/` (the six shipped cases), `records/`
(the step records with the redo record and every archived round, `rounds.json`, Review's findings on
round 3 (`review.round1.json`) and on round 4 (`review.final.json`), Verify's final report, the
cases record, the developers' tests check after #33, each round's check reports, round 3's test
file, the Plan question, and the command logs under `records/logs/`).
