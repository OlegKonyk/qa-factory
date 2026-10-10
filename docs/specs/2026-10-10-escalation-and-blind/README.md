# Build specs, 2026-10-10: stronger models before people, and blind mode

What these slices build, in the order Oleg asked for (`docs/next-session.md`, `docs/decisions.md`
2026-10-10):

1. **The escalation inside Verify.** When lint, the revert check or mutation fails because of the
   generated tests, the test writer gets the findings for one repair round in a fresh session and
   the checks run again from lint. If a check still fails, a stronger model (`claude-fable-5-1`,
   headless, read-only tools) reads the check reports and decides: `retry` with its guidance (one
   more writer round), `change_is_wrong` (the tests are right, the change is wrong: terminal fail
   with its diagnosis), `environment` (terminal fail with its diagnosis), or `cannot_decide`
   (the only outcome that stops for a person). Its answer is recorded in the run folder.
2. **The Review fix round.** When Review requests changes, the writer gets the findings for one fix
   round, Verify's checks run again, and Review runs once more.
3. **Caps per ticket.** Writer rounds, stronger-model calls and model spend are capped per ticket
   and recorded in `<run_dir>/rounds.json`, which survives re-runs of the driver.
4. **Blind mode** (`"qa_mode": "blind"` in the ticket). Frame, Plan and the first test writer
   run in the base worktree, without the change, the developers' tests or the ticket's provenance
   (`base`, `head`, `source`), and with read access to every other copy of the application denied.
   The tests are then moved into the head worktree and every check runs unchanged.
5. **A run summary** (`python -m factory summary <run_dir>`): the numbers track 1 compares.

| Slice | Files | Spec |
|---|---|---|
| S1 caps and the stronger model | `factory/rounds.py`, `factory/escalate.py`, `factory/prompts/escalate.md`, `tests/test_rounds.py`, `tests/test_escalate.py` | `s1-rounds-escalate.md` |
| S2 blind plumbing | `factory/blind.py`, `factory/headless.py`, `factory/prompts/frame.md`, `factory/prompts/plan.md`, `tests/test_blind.py`, `tests/test_headless.py` (additions only) | `s2-blind.md` |
| S3 the Verify and Review loop | `factory/steps/verify.py`, `factory/steps/review.py`, `factory/prompts/write_tests_repair.md`, `factory/prompts/write_tests_blind.md`, `tests/test_verify_loop.py`, `tests/test_verify_step.py`, `tests/test_prompt_steps.py` (review tests only) | `s3-verify-review.md` |
| S4 the run summary | `factory/summary.py`, `factory/__main__.py`, `tests/test_summary.py` | `s4-summary.md` |

S1, S2 and S4 are independent and are built in parallel. S3 is built after S1 and S2 and uses
their interfaces exactly as written here.

## Rules for every slice

- Python 3.13, standard library only in the factory. Match the surrounding code: module docstring
  that says what the module is for, short functions, plain names, comments only where the reason
  is not obvious. ruff config in `pyproject.toml` (line length 110).
- Tests in the existing style: pytest, `tmp_path`, an injected `runner` instead of real `claude`
  calls (see `tests/test_headless.py`, `tests/test_prompt_steps.py`), monkeypatched `CHECKS` for
  Verify (see `tests/test_verify_step.py`). No real model call, no network, no linkding needed.
- Run and paste: `uv run pytest <your test files> -q`, then `uv run pytest -q` (the whole suite),
  `uv run ruff check factory tests targets`, `uv run ruff format --check factory tests targets`.
- Touch only the files of your slice. No git commands that change state (no commit, checkout,
  stash, reset).
- Never print, copy or search for the local term list used by `hooks/guard.sh`.
