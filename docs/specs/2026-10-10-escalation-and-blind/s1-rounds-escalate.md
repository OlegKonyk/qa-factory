# S1: caps per ticket, and the stronger model's decision

Files: `factory/rounds.py`, `factory/escalate.py`, `factory/prompts/escalate.md`,
`tests/test_rounds.py`, `tests/test_escalate.py`. Read first: `factory/headless.py` (the `call`
function and `Result`), `factory/steps/verify.py` (how a headless call is made today).

## factory/rounds.py

The per-ticket record of model rounds and spend, kept in `<run_dir>/rounds.json` so that the caps
hold across re-runs of the driver (a failed Verify re-run must not get fresh caps).

```python
DEFAULT_CAPS = {"writer_rounds": 3, "advice": 2, "usd": 15.0}
MIN_CALL_USD = 0.50          # a cold headless call costs about 0.10 USD; below this, do not start one
WRITER_ROUND_KINDS = ("repair", "guided", "review_fix")

class CapReached(Exception):
    """A model call would exceed the ticket's spend cap."""

def caps_for(ticket: dict, app: dict) -> dict:
    """DEFAULT_CAPS, overridden by app.get("caps"), overridden by ticket.get("caps"). Unknown keys kept."""

class Ledger:
    def __init__(self, run_dir, caps: dict | None = None): ...
```

- `Ledger(run_dir, caps)`: loads `<run_dir>/rounds.json` if it exists (keeps its entries), and sets
  the caps to `caps` if given, else the file's caps, else DEFAULT_CAPS. Does not write until `add`.
- `path` (Path), `caps` (dict), `entries` (list of dicts).
- `add(step, kind, cost_usd, model="", duration_s=0.0, round=None, outcome="") -> dict`: appends
  `{"at": <ISO UTC>, "step", "kind", "round", "cost_usd", "model", "duration_s", "outcome"}` and
  writes the file at once (indent 1): `{"caps": ..., "entries": [...], "spent_usd": <sum, 4 dp>}`.
- `spent() -> float`: sum of `cost_usd` over entries.
- `count(*kinds) -> int`: entries whose kind is in `kinds`.
- `rounds_left() -> int`: `caps["writer_rounds"] - count(*WRITER_ROUND_KINDS)`, never below 0.
- `advice_left() -> int`: `caps["advice"] - count("advice")`, never below 0.
- `budget_for(default_usd) -> float`: `min(default_usd, caps["usd"] - spent())` rounded to 2 dp;
  raises `CapReached(f"spend cap reached: {spent:.2f} of {cap:.2f} USD spent on this ticket")` when
  that is below `MIN_CALL_USD`. This is what makes the spend cap hard: every model call passes the
  returned value as its `--max-budget-usd`.
- `summary() -> dict`: `{"caps", "spent_usd", "writer_rounds_used", "advice_used", "calls": len(entries)}`.

Kinds used by the callers (S3): `write`, `repair`, `guided`, `review_fix`, `advice`, `cases`,
`cases_repair`, `review`.

## factory/escalate.py

```python
MODEL = os.environ.get("QA_FACTORY_ADVICE_MODEL", "claude-fable-5-1")
BUDGET_USD = float(os.environ.get("QA_FACTORY_ADVICE_BUDGET", "3.00"))
TOOLS = "Read,Glob,Grep"
DECISIONS = ("retry", "change_is_wrong", "environment", "cannot_decide")

def decide(*, ticket: dict, strategy: str, diff: str, failure: dict, history: list[dict],
           test_files: list[str], head_tree: str, run_dir: str, allow_retry: bool,
           budget_usd: float, out_path: str, runner=subprocess.run) -> dict:
```

Asks the stronger model what to do about a check that still fails after the writer's repair round,
writes the answer to `out_path` (JSON, indent 1) and returns it.

- `failure` is `{"check": <name>, "reason": <one line>, "report": <path to that check's JSON for
  the failing round, may be "">}`. `history` is a list of `{"round": n, "kind": ..., "failure":
  <reason or None>}` describing what was tried. `test_files` are paths relative to `head_tree`.
- The allowed decisions are DECISIONS without `retry` when `allow_retry` is False. The JSON schema
  passed to the call is `{"type": "object", "properties": {"decision": {"type": "string", "enum":
  <allowed>}, "why": {"type": "string"}, "guidance": {"type": "string"}, "diagnosis": {"type":
  "string"}}, "required": ["decision", "why", "guidance", "diagnosis"]}`.
- The prompt is `factory/prompts/escalate.md` filled with `str.format_map`: `ticket_json`
  (json.dumps(ticket, indent=1)), `strategy`, `diff`, `check`, `reason`, `report`, `history_json`,
  `test_files` (one per line, "- path"), `run_dir`, `decisions` (the allowed ones, comma-separated).
  Note the prompt contains literal JSON braces nowhere, or escapes them as `{{ }}`.
- The call: `headless.call(prompt, cwd=head_tree, model=MODEL, budget_usd=budget_usd, tools=TOOLS,
  allowed_tools=TOOLS, schema=schema, add_dirs=[run_dir], runner=runner)`.
- The record written and returned:
  `{"decision", "why", "guidance", "diagnosis", "allowed": [...], "failure": failure,
  "history": history, "metrics": result.metrics(), "is_error": result.is_error, "model": MODEL}`.
- If the call errored, gave no structured output, or gave a decision outside the allowed ones, the
  record's decision is `cannot_decide` and `why` says so ("the stronger model gave no usable
  answer: " + the first 300 characters of the result text or stderr). Never raise for a model
  failure; raise only for a programming error.

## factory/prompts/escalate.md

Plain English, short. It says, in this order:

- You are the senior engineer the QA factory consults when its checks still fail after the test
  writer has had a repair round. You read; you do not change files.
- The ticket, the test strategy, the change (diff), the failing check and its one-line reason,
  where the full report is (`{report}`; the run folder `{run_dir}` holds every round's reports
  under `verify/rounds/`), the generated test files (relative to the working directory, which is
  the application at the commit with the change), and what was tried (`{history_json}`).
- Decide exactly one of `{decisions}`:
  - `retry`: the tests are wrong or weak and you can say how to fix them. `guidance` is concrete
    instructions for the test writer (which test, what to change, why). The writer will not see
    this conversation; write guidance that stands alone.
  - `change_is_wrong`: the tests check the ticket's acceptance criteria correctly and the change
    does not meet them. `diagnosis` names the criterion, the test and the evidence.
  - `environment`: the failure comes from the machine, the tools or the application's setup, not
    from the tests or the change. `diagnosis` says what and how to fix it.
  - `cannot_decide`: only when the evidence does not let you choose. `why` says what a person must
    look at.
- Fill all four fields; use an empty string for a field that does not apply. Respond only through
  the structured output.

## Tests (tests/test_rounds.py, tests/test_escalate.py)

- Ledger: caps_for merge order; add writes the file and a new Ledger on the same folder sees the
  entries (resume); spent/count/rounds_left/advice_left; budget_for returns the min and raises
  CapReached below MIN_CALL_USD; caps given to the constructor replace the file's caps.
- decide, with a fake runner returning canned headless JSON (copy the `canned` helper idea from
  `tests/test_prompt_steps.py`): each of the four decisions is returned and written to out_path;
  with allow_retry False the schema enum in argv has no "retry"; a model error, a missing structured
  output and a decision outside the allowed set each become `cannot_decide`; argv carries
  `--model claude-fable-5-1`, `--tools Read,Glob,Grep`, `--add-dir <run_dir>`, the budget, and
  cwd is head_tree; the prompt contains the check name, the reason and the ticket title.
