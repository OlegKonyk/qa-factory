# S2: blind-mode plumbing (the helpers, the headless transcript, Frame and Plan)

Files: `factory/blind.py` (new), `factory/headless.py`, `factory/prompts/frame.md`,
`factory/prompts/plan.md`, `tests/test_blind.py` (new), `tests/test_headless.py` (add tests, do not
change existing ones unless an argv assertion must change). Read first: `factory/headless.py`,
`factory/steps/frame.py`, `factory/steps/plan.py`, `factory/driver.py` (`_load_repo`: what
`repo` holds), `targets/linkding/app.json`.

Blind mode is a ticket field: `"qa_mode": "blind"`. It means the QA side works from the ticket
and the code before the change only. Measured on this machine (2026-10-10, Claude Code 2.1.296):
a settings file with `{"permissions": {"deny": ["Read(//abs/path/**)", "Bash(git *)"]}}` passed
with `--settings` makes a headless session's Read of a file under `/abs/path` and its `git log`
both come back denied (in `permission_denials`). A deny path needs the double slash: a single
leading slash is read relative to the settings file and did not deny.

## factory/blind.py

```python
HIDDEN_FIELDS = ("base", "head", "source", "app", "caps", "gate", "qa_mode")

def is_blind(ticket: dict) -> bool:
    """True when the ticket asks for tests written without seeing the change."""

def public_ticket(ticket: dict) -> dict:
    """The ticket as a blind session sees it: without HIDDEN_FIELDS (the commits and the provenance
    would point at the change)."""

def hidden_paths(repo: dict, factory_root) -> list[str]:
    """Absolute, resolved paths a blind session must not read.

    - repo["app"]["repo"]: the application's clone (its checkout holds later code);
    - repo["head_tree"]: this ticket's head worktree;
    - every directory two levels under repo["app"]["worktrees"] (<worktrees>/<ticket>/<base|head>)
      except repo["base_tree"]: other tickets' trees hold other changes and generated tests;
    - factory_root: the factory's repository (run folders and docs/runs hold earlier tests).
    Paths that do not exist are still listed when named directly (repo, head_tree, factory_root);
    the worktree scan lists only what exists. Sorted, no duplicates, never the base tree itself.
    """

def settings(hidden: list[str], base: dict | None = None) -> dict:
    """Claude Code settings that deny a blind session the hidden paths and git.

    A deep copy of `base` (or {}), with permissions.deny extended by, for each hidden path p:
    f"Read(/{p}/**)", f"Grep(/{p}/**)", f"Glob(/{p}/**)", f"Edit(/{p}/**)", f"Write(/{p}/**)"
    (p is absolute, so this gives the double slash), and then "Bash(git *)" and "Bash(git)".
    Existing deny entries of `base` are kept first; no duplicates.
    """

def audit(transcript_path, hidden: list[str]) -> dict:
    """Read a stream-json transcript and report every tool call that named a hidden path or ran git.

    Each line is a JSON object; tool calls are the items with "type": "tool_use" inside
    message.content of lines with "type": "assistant". A call is flagged when json.dumps(its input)
    contains any hidden path, or when it is a Bash call whose command starts with "git" (after
    stripping leading whitespace, or after "cd <dir> &&"). Unparseable lines are skipped.
    Returns {"tool_calls": <count>, "flagged": [{"tool", "input": <first 300 chars of json.dumps(input)>}],
    "clean": <no flagged call>, "transcript": str(transcript_path)}. A missing transcript returns
    {"tool_calls": 0, "flagged": [], "clean": False, "transcript": ..., "error": "no transcript"}.
    """

WHERE_SEQUENTIAL = "You are in the working tree of the changed code. You may read the developers' own tests."
WHERE_BLIND = (
    "You are in the working tree of the code before the change. The change does not exist yet and "
    "you cannot see it; there are no developers' tests for it. Work from the ticket and the code as "
    "it is now, and do not look for the change anywhere else."
)
```

## factory/headless.py

1. `call(..., transcript_path: str | Path | None = None)`: when given, the session runs with
   `--output-format stream-json --verbose` instead of `--output-format json`, its stdout is written
   to `transcript_path` (parent folders created), and the result is parsed from the last line whose
   JSON object has `"type": "result"` (fall back to the existing `parse_output`). `build_argv`
   gains `stream: bool = False` for this. With no transcript nothing changes (existing tests stay
   green unchanged).
2. `one_prompt(...)` gains blind mode, decided by `blind.is_blind(inp["ticket"])`:
   - cwd: `repo["base_tree"]` when blind, `repo["head_tree"]` otherwise;
   - `ticket_json`: `json.dumps(blind.public_ticket(ticket), indent=2)` when blind, the full ticket
     otherwise;
   - `diff`: always "" when blind (Frame and Plan run before Implement, so it is empty today anyway;
     make it explicit);
   - `where`: `blind.WHERE_BLIND` or `blind.WHERE_SEQUENTIAL`, a new prompt value;
   - `settings`: `blind.settings(blind.hidden_paths(repo, FACTORY_ROOT))` when blind, None otherwise;
     pass it to `call`.
   - A new keyword `budget_usd` already exists; also accept `cwd: str | None = None` to override the
     tree (Review uses the head tree in every mode and passes nothing; keep its behaviour).
   - Review calls `one_prompt` too. Review runs after the join, so it must never be blind: add a
     keyword `allow_blind: bool = True`; Review will pass False (S3 does that edit; here just add the
     keyword and honour it).
3. `factory/prompts/frame.md` and `plan.md`: replace the sentence "You are in the working tree of
   the changed code." (and, in plan.md, "You may read files, including the developers' own tests.")
   with `{where}` plus "Do not write code and do not change files. You may read files." In plan.md
   change "cover the acceptance criteria the developers' own tests leave uncovered" to "cover the
   acceptance criteria that the developers' own tests, where you can see any, leave uncovered".
   `review.md` is not touched, but `one_prompt` fills `where` for every prompt, so it must not
   break a prompt that has no `{where}` (format_map ignores unused keys; check it).

## Tests (tests/test_blind.py, additions to tests/test_headless.py)

- public_ticket drops exactly HIDDEN_FIELDS and keeps title, description, acceptance criteria.
- hidden_paths on a tmp layout (`wt/t-1/base`, `wt/t-1/head`, `wt/t-0/base`, `wt/t-0/head`, a fake
  clone dir, a fake factory root): lists the clone, both trees of t-0, t-1/head and the factory
  root, and never t-1/base.
- settings: deny entries use `//` for absolute paths, include `Bash(git *)`, keep a base's entries.
- audit on a small hand-written stream-json file: a Read of a hidden path and a `git log` Bash call
  are flagged, a Read under the base tree is not; counts are right; a missing file gives the error.
- headless: with `transcript_path`, argv has `stream-json` and `--verbose` and no `json` format;
  stdout (several JSON lines, the last a `{"type": "result", ...}` object) is saved to the file and
  the Result is parsed from the result line.
- one_prompt (through `frame.run` with an injected runner, as in tests/test_prompt_steps.py):
  sequential: cwd is the head tree, no `--settings`, prompt has the WHERE_SEQUENTIAL text and the
  full ticket. Blind: cwd is the base tree, `--settings` file holds the deny rules (the FakeRunner
  in tests/test_headless.py reads it), the prompt has WHERE_BLIND and no "base"/"head"/"source"
  keys or values from the ticket.
