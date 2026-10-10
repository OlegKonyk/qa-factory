# S4: the run summary

Files: `factory/summary.py` (new), `factory/__main__.py` (a `summary` subcommand),
`tests/test_summary.py` (new). Read first: `factory/driver.py` (`status`),
`factory/envelope.py`, `factory/checks/revert.py` (`run`'s report: `tests` maps a pytest node id
to `{at_head, reverted, verdict, message}`; verdicts are proves-behaviour,
passes-without-change, head-fails, missing-name, crash, skip), `factory/checks/mutants.py` (`run`'s
report: generated, checked, killed, survived, score, on_changed_lines {checked, killed, survived,
score}), `docs/runs/2026-10-08-linkding-sort-by-modified/records/` (a real run folder: steps/,
verify/, review/, ship/).

`python -m factory summary <run_dir> [<run_dir> ...] [--json <path>]` prints, for one or several
run folders, the numbers the exploration's track 1 compares, and writes them as JSON (default
`<run_dir>/summary.json` for a single run; with several runs, only when `--json` is given).

## What is read

- `steps/0N-<name>.json` (the current record of each step) and `steps/0N-<name>.round<k>.json`
  (earlier failed runs of a step): status, duration_s, output.metrics (`cost_usd`, `model`,
  `time_s`, `costs`).
- `verify/report.json`: may have `rounds` (list of `{round, kind, checks, failure}`), `ledger`,
  `blind`, `blind_audit`. The first run of 2026-10-08 has no `rounds`: then its single round is the
  top-level `verify/revert.json` and `verify/mutation.json`.
- `verify/rounds/<n>/revert.json` and `.../mutation.json` per round (the check's JSON as dumped:
  `{"status": "pass", "result": <report>}` or `{"status": "fail", "reason": ...}`; read the
  `result` when present).
- `rounds.json` (the ticket's model rounds and spend), `verify/escalation-*.json` (decisions).
- `ticket.json` for the id and `qa_mode` (absent means sequential).

## What is computed, per run

```
{
  "ticket": id, "qa_mode": "blind" | "sequential",
  "first_round": <round numbers>, "final_round": <round numbers>,   # same object when one round
  "rounds": [{round, kind, failure}], "decisions": [<escalation decision strings>],
  "stages": {name: {"status", "duration_s", "cost_usd", "model"}},   # frame..ship, current records
  "verify_parts": {"time_s": {...}, "cost_usd": {...}},               # from verify's metrics
  "spend_usd": <sum of cost_usd over the current step records>,
  "ledger": <rounds.json summary or null>,
  "blind_audit": <report's blind_audit or null>,
}
```

Round numbers (`null` for anything the round did not reach):

- `tests`: number of entries in the revert report's `tests`; `tests_api` and `tests_browser`
  split by the node id's file name (`e2e_test_` prefix means browser);
- `pass_at_head`: entries with `at_head == "pass"`;
- `fail_at_base_on_assertion`: verdict `proves-behaviour`;
- `pass_on_both`: verdict `passes-without-change`;
- `missing_name`, `crash`, `head_fails`: those verdicts;
- `mutation`: per set name (generated, generated_and_developers, developers when present):
  `{checked, killed, score, changed_lines: {checked, killed, score}}`.

## Output

A plain Markdown table on stdout, one row per number and one column per run (column header = the
ticket id), then the stage table (duration and spend per step), then the rounds and decisions, so
a person can paste it into a document. Numbers as measured; a missing value prints as "-".

## Tests (tests/test_summary.py)

- Build a small run folder in tmp_path by hand: two step records, a verify/report.json with two
  rounds, `rounds/1/revert.json` with one proves-behaviour, one head-fails and one crash test (one
  of them an `e2e_test_` file), `rounds/2/revert.json` all proves-behaviour, a mutation JSON, a
  rounds.json, an escalation file. Check every computed number and that the table has the ticket
  id as a column.
- A run folder shaped like the first run (no `rounds` in report.json, top-level revert.json and
  mutation.json): first_round and final_round are the same and computed from the top level.
- Two run folders side by side: one column each.
- If `docs/runs/2026-10-08-linkding-sort-by-modified/records` exists, summarize it and check the
  numbers the status file states: 6 tests, 5 fail at base on an assertion, 1 passes on both, the
  generated set kills 27 of 108 and 10 of 10 on the changed lines.
