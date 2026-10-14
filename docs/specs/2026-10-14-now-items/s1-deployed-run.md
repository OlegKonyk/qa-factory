# s1 · Run a shipped feature's tests against linkding from its Docker image

Worktree: `~/dev/qa-factory-wt/deployed` (branch `feat/deployed-run`). Work only there. Docker
runs on this laptop through colima (checked today: server 29.5.2, running). Image
`sissbruecker/linkding:1.47.0` is pulled; release 1.46.0 is the first that contains both shipped
linkding features (sort by modified, `0490013`; bundle filters, `573b6f5`), checked with
`git tag --contains` in the factory's linkding clone. No factory model call.

## The question (roadmap item 1, `docs/trust.md` second verification point)

The factory's tests are written and checked inside the application's own suite (data through the
ORM, Django's test client, `LiveServerTestCase`). Can the same cases run against a deployed
instance, with its data created through the public REST API only? What has to change, and why?

## Step 1: the deployed application, measured

1. Start it: `docker run -d --name qa-factory-linkding -p 9090:9090 -e LD_SUPERUSER_NAME=qa
   -e LD_SUPERUSER_PASSWORD=<pick one> sissbruecker/linkding:1.47.0`. Wait until
   `GET http://127.0.0.1:9090/health` answers. Record the time from `run` to healthy.
2. The API token: `docker exec qa-factory-linkding python manage.py shell -c "..."`, reading the
   token of user `qa` from `rest_framework.authtoken.models.Token` (`get_or_create`). This is
   environment setup, not test data; say so in the README.
3. **Check before building on it:** create a bookmark through `POST /api/bookmarks/`, read its
   `date_modified`, `PATCH` its title, read again. Does `date_modified` move forward? With what
   resolution? (The in-suite tests set `date_modified` directly on the model; the API has no way to
   set it, so the thin suite must build the modified order through edits.) Record the answer. If it
   does not move, stop and report.

## Step 2: the thin suite

Location: `targets/linkding/deployed/` in the factory repository: `conftest.py`,
`test_sort_by_modified.py`, `README.md`. Dependencies: a new dependency group `deployed` in
`pyproject.toml` with `pytest-playwright` (current release), installed with `uv sync --group
deployed` and `uv run --no-sync playwright install chromium`; the factory's own `dev` group and
`just check` stay as they are (the new tests must not be collected by `uv run pytest` from the
root: keep `testpaths = ["tests"]`; run the thin suite by path).

The cases to port are the readable cases of the shipped run,
`docs/runs/2026-10-10-linkding-sort-by-modified-blind/testcases/TC-bookmarks-001.md` to `004.md`
(its in-suite tests are beside them under `tests/`). One pytest test per case, named for it, with
the case id in a comment or marker.

- Configuration from the environment: `LINKDING_URL` (default `http://127.0.0.1:9090`),
  `LINKDING_TOKEN`, and for the browser case `LINKDING_USER`, `LINKDING_PASSWORD`. Missing
  variables skip with a clear message.
- API cases (001, 002, 003) through Playwright's `APIRequestContext` (the project's
  `py-testing:testing-playwright-api` skill: a session-scoped request fixture with the base URL
  and the `Authorization: Token ...` header, a small client class). Data through the API only:
  three bookmarks (plus the archived three for 002) with a run-unique marker in their titles or a
  run-unique tag, modified in the order the case needs through `PATCH`, each edit confirmed by
  reading `date_modified` back as strictly greater than the previous one (no fixed sleeps longer
  than needed; wait on the value, not the clock). Scope every list request with `q=<marker>`
  beside `sort=...`, so "exactly three results" holds on an instance that has other data. Delete
  what the test created at the end, also on failure. The "other user's bookmark" precondition of
  case 001 cannot be created with one token: say so in the README and drop that precondition
  from the ported test, or create a second user through `manage.py` if that stays environment
  setup; your call, recorded.
- Browser case (004) through pytest-playwright's `page`: log in through the form with the user
  and password, then the steps of the case, with the data created through the API by the same
  fixtures. Role and label locators first (`py-testing:testing-playwright-browser`). Scope the
  list with the marker through the search box or the `q` query parameter.
- Timing: print or record the suite's wall time (`pytest --durations=0` is enough).

## Step 3: run it, record what it took

- Run the suite against the container; paste the command and the full output (pass count,
  durations). Run it twice to show it is repeatable on an instance that already holds the first
  run's leftovers if cleanup failed, or clean data otherwise.
- `targets/linkding/deployed/README.md`: how to start the instance (the exact commands), the
  environment variables, the command to run the suite, the table case → test → result, and
  **what had to change from the in-suite tests and why** (one line per change: `date_modified`
  through edits, scoping by marker, no other user, login instead of a test client, anything else).
- The agent-friendly checklist, `docs/exploration.md` "What makes a repository agent-friendly for
  this loop" (12 items): for each item, did this run need it, and did linkding have it? A table in
  your report; the session folds it into the docs.
- Stop and remove the container at the end (`docker rm -f qa-factory-linkding`), after the runs.

## Evidence

Paste: the measurement of step 1 (start-up time, the `date_modified` probe), the suite's output
twice, `uv run --no-sync ruff check factory tests targets` and `ruff format --check` (add the new
folder to both commands and make it clean), and `uv run --no-sync pytest` still green.

## Report

Files changed; commands and output; the two tables; deviations with reasons; what was left alone.
Do not commit.
