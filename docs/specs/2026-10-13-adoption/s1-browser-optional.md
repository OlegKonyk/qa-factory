# S1: the browser test folder is optional

An application recipe (`targets/<app>/app.json`) may have no browser tests in Python: a plain API
microservice, or isso, whose browser tests are JavaScript in a Docker testbed. Today the factory
requires `browser_tests_dir` and `browser_test_files` everywhere. After this change a recipe may
omit both keys (or set them to `null`), and every step treats the application as API-only.

Files: `factory/steps/verify.py`, `factory/steps/implement.py`, `factory/steps/ship.py`,
`factory/checks/revert.py` (only if needed: `browser_glob` may already be `None`; check and keep),
`factory/prompts/write_tests.md`, `factory/prompts/write_tests_blind.md`,
`factory/prompts/write_tests_repair.md`, `factory/report.py` and `factory/summary.py` only if they
read those keys, and tests under `tests/`. Do not edit anything else. Read first:
`targets/linkding/app.json` (the recipe shape), `factory/steps/verify.py` (`_in_test_dirs`,
`_clean_tests`, `_writer_prompt`, `write_tests`, `run_revert`, `run_mutation`), `implement.py`
lines 40-80, `ship.py` lines 90-100, and `tests/test_verify_step.py` plus `tests/test_ship.py` for
how existing tests build a recipe.

## Behaviour

1. Add one helper in `factory/steps/verify.py`, `browser_dir(app)`, returning
   `app.get("browser_tests_dir") or None`, and use it (or an equivalent local check) in every place
   that reads `browser_tests_dir` or `browser_test_files` in the four modules above. With no browser
   folder:
   - `_in_test_dirs`, `_clean_tests`, `implement._is_test` and the `git diff` excludes in
     `implement.py` consider only the API folder;
   - `ship.py` runs only the recipe's suite invocations (no browser invocation);
   - `run_revert` passes `browser_glob=None`;
   - the writer prompts carry no browser instructions. Do this by building the prompt sections in
     `_writer_prompt`: a value `browser_section` for "How to work" that is either the current
     browser wording or a line "This application has no browser tests in Python: write API tests
     only." and no browser file name. Keep the prompts' meaning for linkding unchanged; the three
     linkding runs' prompts must still render (the existing prompt tests prove it).
2. The writer check "wrote no API test file" stays. Nothing new fails when no browser file is
   written, with or without a browser folder (it is already optional in practice).
3. `targets/linkding/app.json` stays as it is.

## Tests (in the existing files, same style)

- A recipe without the two keys: `_in_test_dirs` and `_clean_tests` touch only the API folder;
  `implement.run` classifies a changed file under a folder named like a browser folder as source,
  not test; `ship.run` makes one suite invocation.
- `_writer_prompt` for a recipe without the keys, in fresh, blind and repair modes: the rendered
  prompt contains "API tests only" and no `{browser` placeholder is left unrendered (assert no
  `{` followed by `browser` and no `None` in the text).
- A recipe with the keys renders exactly as before (the existing tests stay green unchanged).

## Definition of done

`just check` green (it runs ruff and the 213 tests; expect a few more). Paste the full output of
`just check`. Report every file changed, and any place that reads the browser keys you decided
not to change, with the reason.
