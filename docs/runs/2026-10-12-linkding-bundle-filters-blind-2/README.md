# The bundles ticket, blind, a second time, on Restate (2026-10-12)

The first real ticket run through the Restate workflow (`--engine restate`), on the laptop. It is
the same ticket as `docs/runs/2026-10-10-linkding-bundle-filters-blind/`, written again by a fresh
blind writer under a new id. Every model call was billed to the Console API key, not the
subscription (`docs/decisions.md`, 2026-10-12).

```
restate-server --base-dir ~/Library/Caches/qa-factory/restate &
scripts/with-console-key.sh uv run python -m factory restate serve &     # the steps run here
uv run python -m factory restate register
uv run python targets/linkding/fetch.py --ticket targets/linkding/tickets/bundle-filters-blind-2.json --prepare-e2e
uv run python -m factory run targets/linkding/tickets/bundle-filters-blind-2.json --engine restate
uv run python -m factory restate answer linkding-bundle-filters-blind-2 <answer.json>
```

All numbers below are measured.

| step | result | time | model spend |
|---|---|---|---|
| Frame | pass | 14.1 s | in the total |
| Plan | pass | 12.9 s | in the total |
| Implement | pass (the developers' commit 573b6f5: 7 source and 6 test files) | 0.07 s | none |
| Verify | every check passed in round 1; stopped at the ticket's person-gate | 16 min 7 s | 3.43 USD writer, 1.51 USD readable cases |
| Gate | answered over HTTP 35 s after it opened (below) | | |
| Review | approve, six low findings | 81.8 s | 0.40 USD |
| Ship | committed `bf01f41` on `qa/linkding-bundle-filters-blind-2`; linkding's suite with the new tests: 1280 passed, and 2 browser tests passed | 30.8 s | none |

From submit (17:14:53) to the end (17:34:16): 19 min 23 s, which includes the 35 s at the gate.
The total model spend was 5.44 USD (`summary.md`), under the ticket's 8 USD cap.

**The tests.** The blind writer produced 7 tests: 5 API and 2 browser.
- **Old code:** all 7 fail on the code before the change, on an assertion. So every test proves the change, and none is a regression guard.
- **The change:** all 7 pass with the developers' change.
- **Mutation testing** on `_filter_bundle`, 82 mutants:
  - the generated tests kill 51 (62 %);
  - on the 16 changed lines they kill all 16;
  - the developers' own tests kill 77 (94 %), also 16 of 16 on the changed lines.

**The gate.** The ticket sets `"gate": "person"`, so Verify parked the run on the durable promise `verify-1`. The laptop session answered it with `records/steps/04-verify.answer1.json`, as the 2026-10-10 decision allows: approval of passing work is automatic, and Oleg is not asked. The answer names the session, not Oleg.

**Review's six low findings, none blocking:**
- PUT is untested.
- `any_tags` is not combined with the new fields.
- Values outside off/yes/no are not tested.
- The HTML page checks only the yes/yes and no/no bundles.
- A count helper that does not retry is safe only because of the order of the assertions.
- One browser test reads the bundle id from the database, not the UI.

**Beside the first blind run of the same ticket** (2026-10-10, its first round):

| | 2026-10-10 | 2026-10-12 |
|---|---|---|
| tests | 13 | 7 |
| tests failing on the old code on an assertion | 12 | 7 |
| mutants killed, whole function | 64 of 82 (78 %) | 51 of 82 (62 %) |
| mutants killed, changed lines | 16 of 16 | 16 of 16 |
| repair round or stronger model needed | yes (the factory's own check was wrong) | no |
| ended | at the cap, before the readable cases | shipped |
| spend | 8.47 USD | 5.44 USD |

Two blind writers on one ticket wrote different suites. Both caught every mutant on the changed lines, but the first was stronger on the rest of the function. One pair is not a trend.

- `tests/`: the 7 tests as written. `testcases/`: the 7 readable cases.
- `records/`: the run folder without the mutation and revert workspaces, the lock files or the writer's raw transcript. That transcript stays local because it holds this machine's hook output.
- `report.md`: `python -m factory report records`. `summary.md` and `summary.json`: `python -m factory summary records`.
- The Restate UI during this run: `../2026-10-12-restate-laptop/ui-journal-real-verify-running.png` and `ui-journal-real-parked-at-gate.png`.
