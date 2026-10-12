# R1: the run report

Files: `factory/report.py` (new), `factory/__main__.py` (a `report` subcommand, only that),
`tests/test_report.py` (new). Do not edit any other file. Read first: `factory/summary.py` (it
already computes the numbers; reuse `summary.summarize()`, do not recompute what it gives),
`tests/test_summary.py` (how its tests build run folders), `factory/checks/revert.py` and
`factory/checks/mutants.py` (the shapes of their reports), and the three committed run folders:

- `docs/runs/2026-10-08-linkding-sort-by-modified/records/` (one Verify round, no `rounds`; its
  test cases are committed beside it in `../testcases/`)
- `docs/runs/2026-10-10-linkding-sort-by-modified-blind/records/`
- `docs/runs/2026-10-10-linkding-bundle-filters-blind/records/` (three rounds under
  `verify/rounds/<n>/`, stopped at its spend cap before the test cases; an escalation answer)

## The command

`python -m factory report <run_dir> [--out <path>]` writes one Markdown page, the QA evidence of
one ticket that Restate's UI does not show, to `<run_dir>/report.md` by default (or `--out`), and
prints the path. Exit 0; exit 2 with a message when `<run_dir>/steps` is not a folder.

## What the page holds, in this order

1. **Title and one-line outcome**: the ticket id and title, qa mode, and how the run ended: the
   status of each of the six steps from the step records (`pass`, `fail` with its reason,
   `needs_person` with its question, or `not run`).
2. **Tests**: one row per generated test from the final round's revert report (`tests` maps a pytest
   node id to `{at_head, reverted, verdict, message}`): file, test name, kind (API or browser:
   `e2e_test_` file prefix means browser), result with the change (`at_head`), verdict without it
   (proves-behaviour, passes-without-change, missing-name, crash, head-fails, skip) in plain words,
   and the first line of the failure message on the old code, trimmed to 100 characters. Then the
   counts from `summarize()["final_round"]`.
3. **Readable test cases**: one row per case file listed in `verify/test_cases.json`
   (`result.files`), with the case's title (its first Markdown heading) and a relative link.
   Records hold absolute paths of the laptop they ran on (`/Users/...`); never open those. Look
   for each file at `<run_dir>/verify/testcases/<file>`, then `<run_dir>/../testcases/<basename>`;
   a file found in neither is listed as "not in this folder". No `test_cases.json` means the line
   "No readable cases were written" and the reason if the Verify record gives one.
4. **Mutation**: per set (generated, generated_and_developers, developers when present) checked,
   killed, score, and the same on the changed lines, from `summarize()`. Then **surviving
   mutants**: from the final round's `mutation.json`, `result.runs.<set>.mutants`, every entry with
   `status == "survived"`, grouped by set, with its name, source line and whether it is on a changed
   line; the changed-line survivors first and marked. If more than 30 survive in a set, list the
   changed-line ones and the first 30 others, and say how many were left out.
5. **Rounds**: from `summarize()["rounds"]` (round, kind, failure) and the stronger model's
   decisions (`summarize()["decisions"]`); the ledger (`summarize()["ledger"]`: caps, writer rounds
   used, stronger-model calls used).
6. **Time and spend**: the stage table (step, status, duration, cost, model) and the total spend
   `summarize()["spend_usd"]`, labelled "measured, from the run's records".

A value that is absent prints as "-". Never invent a number. Do not call `summary.main` (it writes
`summary.json` into the run folder); call `summarize()`.

## Tests

`tests/test_report.py`, plain pytest functions, `tmp_path` for every written file:

- Against each of the three committed `records/` folders (copy the folder into `tmp_path` first so
  nothing is written into `docs/`, and copy the sibling `testcases/` folder too where it exists):
  the page names every test from the final revert report, the counts match `summarize()`, the
  surviving mutants listed match a count read straight from `mutation.json`, and for the
  2026-10-08 run the six case titles appear. The bundles run says no cases were written.
- A hand-built minimal run folder (as `tests/test_summary.py` builds them) covering: a step that
  needs a person, a missing `mutation.json`, a case file not found, and more than 30 survivors.
- The command line: `report <dir>` writes `report.md` and exits 0; a folder without `steps/` exits 2.

## Evidence to return

`uv run --no-sync pytest tests/test_report.py -q` output, `uv run --no-sync ruff check factory tests`
and `uv run --no-sync ruff format --check factory tests` clean, and the first 60 lines of the page
generated for `docs/runs/2026-10-10-linkding-bundle-filters-blind/records` (run it with `--out`
into a temp folder). Another builder is changing `factory/driver.py`, `factory/__main__.py`
(other subcommands) and adding `factory/restate_*` files at the same time: if the whole suite
fails outside `tests/test_report.py`, paste it and do not fix it. In `factory/__main__.py` add only
the `report` subparser and its dispatch line, with as small a diff as possible.
