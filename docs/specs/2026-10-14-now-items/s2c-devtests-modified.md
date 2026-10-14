# s2c · The developers' tests check judges modified tests too

Worktree: `~/dev/qa-factory-wt/fixes` (branch `fix/mutation-resume-devtests`), after s2b.

## The problem

`factory/checks/devtests.py` judges only the tests new at head (`new_test_ids`: present in the
file at head, absent at base). A test the change modified in place (same id, different body) is
not judged, although it is as much "a test written with the change".

## The fix

- `judged_test_ids(head_tree, base_tree, relpath, status) -> dict[str, str]`: every test id at
  head mapped to `"new"` (absent at base) or `"modified"` (present at base with a different
  function AST: compare `ast.dump(node, include_attributes=False)` of the test function, including
  its decorators). Unchanged tests are left out. Keep `new_test_ids` as a thin wrapper if anything
  else imports it (grep first); otherwise replace it.
- `run(...)` judges both kinds. The result gains `"kinds": {test id: "new"|"modified"}`, the
  `counts` gain `"modified_tests"` beside `"new_tests"`, and the `reason` reads like
  "3 of 5 tests by the developers (3 new, 2 modified) fail on the old code on an assertion;
  2 fail only for a missing name". The skipped reason becomes "the change added or modified no
  test".
- Everything that renders the result (`factory/report.py` `_developers_lines`,
  `factory/summary.py` if it reads the counts, `python -m factory devtests` output: one line per
  test, now with the kind) shows the kind. grep for `new_test_ids` and `new_tests` and update every
  reader.
- `docs/adopt.md` section 7, the bullet on the developers' own tests: "the tests the change itself
  added or modified".

## Tests and evidence

- `tests/test_devtests.py`: a modified test is judged and labelled, an unchanged one is not, a
  renamed test counts as new, the counts and the reason text, the printed line shows the kind.
- Paste the last lines of `ruff check`, `ruff format --check` and `pytest`.
- Then the real thing, no model call: `uv run --no-sync python -m factory devtests
  /Users/oleg/dev/qa-factory/.artifacts/runs/linkding-sort-by-modified-blind` and the same for
  `linkding-bundle-filters-blind-2` and `isso-no-cache-comment-views`. Paste the output. The
  developers' commits may have modified tests in place; report how many were found.

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
