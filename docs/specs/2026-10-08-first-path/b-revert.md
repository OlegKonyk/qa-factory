# Slice B: the revert check with its failure sorter, and the lint check

Files: factory/checks/failsort_plugin.py, factory/checks/revert.py, factory/checks/lint.py,
tests/test_revert.py, tests/test_lint.py.

## failsort_plugin.py (a pytest plugin)
Start from the old lab's plugin, read-only at
/Users/oleg/dev/assay/.claude/worktrees/wf_915603f2-4c2-3/scripts/coverage/pytest_failsort.py
(read it; copy what is useful; it is MIT-free internal code of Oleg's). Simplify: the plugin is
loaded with `-p factory.checks.failsort_plugin` (PYTHONPATH carries the factory repo root) and
appends one JSON object per line to the file named by env `QA_FACTORY_FAILSORT_OUT`. Per test
(node id as key) record: kind ("test" | "collect"), outcome (passed | failed | error | skipped),
phase (setup | call | teardown | collect), exc_type (qualified), exc_mro (list of qualified names,
object excluded), message (first 300 chars), frames (list of {"file", "line", "function"} for the
whole traceback, outermost first, no filtering). Also a final {"event": "done", "exitstatus"} line.
Keep it under ~150 lines; no request-capture hooks.

## revert.py
`CAUSES = ("pass", "skip", "missing-name", "behaviour", "crash")`.
`classify(record, test_file, support_paths) -> cause`:
- passed → "pass"; skipped → "skip".
- "behaviour" when "AssertionError" (or a subclass: check exc_mro for a name ending in
  "AssertionError") is in exc_mro AND any frame's file ends with `test_file` or with one of
  `support_paths`. This deliberately counts an assertion raised in a helper or in Playwright's
  `expect` as long as the test file or a support file is somewhere in the traceback.
- "missing-name" when the exception is ImportError/ModuleNotFoundError, NameError (not
  UnboundLocalError), AttributeError whose message contains "has no attribute", TypeError whose
  message contains "unexpected keyword argument" or "missing" + "required", a Django
  NoReverseMatch, or kind == "collect".
- otherwise "crash".
`run(head_tree, base_tree, changed_source, new_test_files, workdir, python, pytest_args,
     test_support, browser_glob, exclude_copy, timeout=900) -> dict`:
1. `at_head`: for each new test file run pytest in `head_tree` with the plugin (one invocation
   per file; add `-o python_files=<browser_glob>` when the file's basename matches it); collect
   causes per test id. Every test must be "pass"; otherwise the report says so.
2. Build `<workdir>/reverted`: copy `head_tree` with `shutil.copytree(..., ignore=...)` skipping
   `exclude_copy` names; then for each entry of `changed_source` ({"path", "status"} with status
   "M" | "A" | "D", none of them test files): "M" → overwrite with `base_tree/path`, "A" → remove,
   "D" → copy from `base_tree`. Tests stay as at head.
3. Run the same files in the reverted tree, collect causes.
4. Per test a verdict: "proves-behaviour" (pass at head, behaviour when reverted),
   "passes-without-change" (pass both), "missing-name", "crash", "head-fails" (not pass at head),
   or the raw cause. `status` is "pass" when no test is missing-name, crash or head-fails and at
   least one proves behaviour; otherwise "fail" with a one-line `reason` listing the offenders.
Report: {"status", "reason", "tests": {id: {"at_head", "reverted", "verdict", "message"}},
"wall_s": {"head", "reverted"}, "reverted_tree": path}. The pytest commands run with
`env` carrying PYTHONPATH=<factory repo root> and QA_FACTORY_FAILSORT_OUT=<workdir>/<n>.jsonl, and
`cwd` = the tree. Timeouts become status "fail" with a reason.

## lint.py
`run(tree, python, files, exclude_dirs=()) -> {"status", "findings": [{"file","line","rule","message"}]}`:
- `python -m ruff check <files>` and `python -m ruff format --check <files>` with cwd=tree (the
  application's ruff config applies); parse `ruff check --output-format json`.
- The assertion check (ast): every function or method whose name starts with `test` must contain
  at least one `assert` statement, or a call whose callee name starts with `assert` or equals
  `expect` (e.g. `self.assertEqual`, `expect(locator).to_be_visible()`), or `pytest.raises`,
  or `self.assertRaises`. Otherwise finding rule "no-assertion".
- Also flag: `time.sleep` calls (rule "sleep") and `unittest.mock.patch` of a name that starts
  with the application's own package when given `app_package` (rule "mocks-own-code").
`status` is "pass" when there are no findings.

## Tests
tests/test_revert.py: fixture trees under tmp_path: `head/app.py` with `def add(a, b): return a + b`,
`head/test_new.py` asserting `add(2, 2) == 4`; `base/app.py` with `return a - b`. With
python=sys.executable and pytest_args=["-p","no:cacheprovider"]: the test proves behaviour,
status pass. Add a test file using a name absent at base (`from app import mul`) → missing-name;
a test that raises ZeroDivisionError at base → crash; a test that passes in both →
passes-without-change; a test that fails at head → head-fails; classify() unit tests for each
rule including a Playwright-shaped record (exc_type "AssertionError", frames in
`.../playwright/sync_api/_generated.py` then the test file) → behaviour, and a helper-shaped
record (frame in a support path only) → behaviour, and an AssertionError with frames only inside
the application → crash. Collect error → missing-name.
tests/test_lint.py: a fixture test file with a test lacking assertions, one using
`self.assertEqual`, one using `expect(x).to_be_visible()`, one with `time.sleep(1)`; run through
`lint.run` with sys.executable (ruff is installed in the factory env) and check findings.
