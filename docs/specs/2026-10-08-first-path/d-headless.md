# Slice D: the headless Claude Code runner, the one-prompt steps, and the linkding target files

Files: factory/headless.py, factory/steps/frame.py, factory/steps/plan.py, factory/steps/review.py,
factory/prompts/frame.md, factory/prompts/plan.md, factory/prompts/review.md,
targets/linkding/app.json, targets/linkding/strategy.md, targets/linkding/tickets/sort-by-modified.json,
targets/linkding/fetch.py, tests/test_headless.py, tests/test_prompt_steps.py.
Do NOT write factory/steps/implement.py, verify.py or ship.py (another slice).

## headless.py
Runs Claude Code (`claude`, version 2.1.295 on this machine) non-interactively, one fresh session per
call. First run `claude --help` and confirm the flags below exist; adapt to what the help says and
record any difference in a module comment.
`call(prompt, cwd, model, budget_usd, tools, allowed_tools, schema=None, settings=None,
      add_dirs=(), timeout_s=1800, binary="claude", runner=subprocess.run) -> Result`
- argv: [binary, "-p", prompt, "--output-format", "json", "--model", model, "--max-budget-usd",
  "%.2f" % budget_usd, "--permission-mode", "dontAsk", "--tools", tools, "--allowedTools",
  allowed_tools, "--no-session-persistence"] + ["--json-schema", json.dumps(schema without the
  "$schema" and "$id" keys)] if schema + ["--settings", <path of a temp JSON file written from
  `settings`>] if settings + ["--add-dir", d] for each add_dir.
- env: a copy of os.environ with every variable whose name starts with CLAUDECODE or CLAUDE_CODE
  removed (a headless call from inside a Claude Code session is otherwise refused; verify this with
  the smoke below and record what you saw). stdin=DEVNULL; cwd=cwd.
- Parse stdout as JSON (the last line that parses as a JSON object, in case of noise). Result
  dataclass: text (the "result" string), structured (the "structured_output" value when present,
  else the result text parsed as JSON when it parses, else None), cost_usd ("total_cost_usd"),
  model (from "modelUsage" keys or "model" if present; else the requested model), turns
  ("num_turns"), duration_ms, session_id, input_tokens / output_tokens (from "usage"),
  is_error (bool), permission_denials (list), returncode, stderr (last 2000 chars), raw (dict).
- `Result.metrics()` → {"cost_usd","model","turns","duration_ms","input_tokens","output_tokens"}.
Smoke (do it once, paste the output): `call("Reply with the single word pong and nothing else.",
cwd=tmp, model="claude-sonnet-5-5", budget_usd=0.05, tools="", allowed_tools="")`; then once with
schema {"type":"object","properties":{"word":{"type":"string"}},"required":["word"]} to learn
where the structured value lands. Record the raw JSON keys you saw in a comment at the top of the
module. If `--tools ""` is rejected, pass "Read" instead and note it.

## The one-prompt steps (frame, plan, review)
Each `run(inp: dict-like StepInput) -> StepOutput-shaped dict` (build the dict by hand:
{"status","artifacts","reason","gate","metrics"}; do not import slice A). Common helper in
headless.py: `one_prompt(name, inp, schema, model, budget_usd, tools, allowed_tools, extra: dict)`
reads `factory/prompts/<name>.md`, fills `{placeholders}` with `str.format_map` on a dict holding
ticket_json (pretty JSON), diff (text of `inp["artifacts"]["change_diff"]` when present, else ""),
strategy (text of the app's strategy file), plus `extra`; calls `call(...)` with cwd =
inp["repo"]["head_tree"]; writes `<run_dir>/<name>/<name>.json` holding {"structured", "text",
"metrics"}; returns pass with artifacts {name: that path} and metrics, or fail with the error when
is_error or structured is None.
- frame: read-only tools "Read,Glob,Grep" (allowed the same), model claude-sonnet-5-5, budget 0.50.
  Schema: {"acceptance_criteria": [{"id": str, "text": str, "testable": bool, "surface":
  "api"|"browser"|"unit"|"none"}], "ambiguities": [str], "summary": str}. Prompt: you are framing
  a ticket for QA on this repository; restate each acceptance criterion as something a test can
  check; name the surface; list ambiguities; do not write code.
- plan: same tools and model, budget 0.50. Schema: {"tests": [{"surface": "api"|"browser",
  "file": str, "name": str, "covers": [str], "reason": str}], "placement_reason": str}. Prompt
  includes the strategy file and the frame artifact (extra["frame_json"] = text of the frame
  artifact when present) and the diff; asks for the smallest set of API and browser tests that
  cover the criteria the developers' own tests leave uncovered, placed by the strategy.
- review: tools "Read,Glob,Grep", model claude-opus-5-5, budget 1.00. Reads the generated test
  files named in inp["artifacts"]["tests_manifest"] (a JSON file: {"files": [relpaths]}) when
  present, else the diff. Schema: {"findings": [{"file","line": int,"severity": "high"|"medium"|
  "low","summary","failure_scenario"}], "verdict": "approve"|"request_changes"}. The step returns
  fail with the high findings in `reason` when verdict is request_changes, else pass.
Prompts are Markdown files with the placeholders; keep each under 60 lines; plain language; say
"respond only through the structured output".

## targets/linkding
- app.json exactly as in common.md.
- strategy.md: the per-application rule the test writer reads. Say: linkding is a Django app with
  a REST API (Django REST framework) and server-rendered pages with Playwright browser tests. New
  coverage goes mostly to the API level as `bookmarks/tests/test_<feature>_api.py` using
  `LinkdingApiTestCase` and `BookmarkFactoryMixin` from bookmarks/tests/helpers.py; one or two
  browser tests per feature for the path a user sees, as `bookmarks/tests_e2e/e2e_test_<feature>.py`
  using `LinkdingE2ETestCase` from bookmarks/tests_e2e/helpers.py; unit tests are the
  implementer's. The application's conventions win over generic pytest style (unittest-style
  classes, the helpers' setup_bookmark and friends, `self.client`). Tests use the public surface
  (query-string parameters, API JSON, visible controls), never the code's constants, and their
  fixtures must make the new behaviour observable (for a sort, the order by the new key must differ
  from the default order). A test must fail on the code before the change for a behavioural reason,
  not a missing name. No sleeps, no mocking of the application's own code. Every placement
  decision is written down with its reason. Running the suite: `python -m pytest -p no:cacheprovider
  -n auto bookmarks/tests` and `python -m pytest -p no:cacheprovider -o python_files=e2e_test_*.py
  bookmarks/tests_e2e/<file>` with the repo's venv.
- tickets/sort-by-modified.json: id "linkding-sort-by-modified"; app "targets/linkding/app.json";
  base 0837b5186979e4a52e75582bd295cc73e43d2612; head 0490013e4f67f0d31ccd764a5cb723dcafaf4acd;
  title "Add sort by modification date option"; description: "The bookmark list can be sorted by
  the date a bookmark was added or by title. Add sorting by the date a bookmark was last modified,
  ascending and descending. The option is available wherever the existing sort options are: the
  sort dropdown of the bookmark list and the `sort` query parameter of the bookmarks REST API
  (`GET /api/bookmarks/?sort=modified_asc` and `sort=modified_desc`), including the archived
  bookmarks list. Taken from linkding pull request #1363 (upstream commit 0490013)."
  acceptance_criteria: ["GET /api/bookmarks/?sort=modified_asc returns the user's bookmarks ordered
  by date_modified ascending", "GET /api/bookmarks/?sort=modified_desc returns them ordered by
  date_modified descending", "The bookmark list page offers 'Modified ↑' and 'Modified ↓' in the
  sort dropdown and selecting one reorders the list accordingly", "The archived bookmarks list and
  its API accept the same two sort values", "An unknown sort value still falls back to the default
  order (added, newest first)"].
- fetch.py (`uv run python targets/linkding/fetch.py [--ticket PATH] [--from LOCAL_MIRROR]
  [--prepare-e2e]`): standard library; clones https://github.com/sissbruecker/linkding into the
  recipe's `repo` when absent (`--from` clones from a local path then sets origin to upstream);
  checks out tag v1.47.0 detached; `uv sync --python 3.13` there; `uv pip install --python
  <repo>/.venv/bin/python mutmut==3.8.0`; with --ticket, creates/updates worktrees `wt/base` and
  `wt/head` at the ticket's commits (`git worktree add --detach`, or `git -C wt/x checkout --detach
  <sha>` when present) and `mkdir -p data/assets data/favicons data/previews` in each; with
  --prepare-e2e runs in wt/head: `npm install --no-audit --no-fund`, `npm run build`,
  `<venv python> manage.py collectstatic --no-input`, `<venv python> -m playwright install
  chromium`. Prints `ok    ...` / `FAIL  ...` lines, exits 1 on any failure, idempotent. Run it for
  real (the clone and worktrees already exist, so it should report ok everywhere without network)
  and paste the output.

## Tests
tests/test_headless.py: argv construction (schema stripped of $schema; settings file written;
add-dir repeated), env scrubbing, parsing a captured result JSON (use the real JSON you captured in
the smoke as the fixture, costs included), is_error path, noisy stdout with a trailing JSON line.
Inject `runner` to avoid real calls. tests/test_prompt_steps.py: frame/plan/review run with an
injected runner returning canned JSON; check the artifact file, the status, the metrics; review
returns fail on request_changes; a prompt file's placeholders all resolve for a sample input
(write the prompts so `str.format_map` works: escape literal braces).
