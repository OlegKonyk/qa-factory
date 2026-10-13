# isso, the no-cache ticket, blind: the second application, shipped (2026-10-13)

The first ticket on a second application: isso, a werkzeug comment server whose tests live inside
the source package (`isso/tests/`), with no Python browser tests. An agent onboarded it by
reading only `docs/adopt.md` (`docs/log.md`, 2026-10-13). The ticket is upstream commit 7e91d59,
which adds `Cache-Control: no-store` to `GET /?uri=` and `GET /id/<id>`; its base is the parent,
9fc7a06. Frame and Plan billed the subscription; everything after billed the Console API key.

```
uv run python targets/isso/fetch.py --ticket targets/isso/tickets/no-cache-comment-views.json
uv run python -m factory run targets/isso/tickets/no-cache-comment-views.json --until implement
scripts/with-console-key.sh uv run python -m factory run targets/isso/tickets/no-cache-comment-views.json
uv run python -m factory status .artifacts/runs/isso-no-cache-comment-views
uv run python -m factory report .artifacts/runs/isso-no-cache-comment-views
uv run python -m factory summary .artifacts/runs/isso-no-cache-comment-views > summary.md
```

All numbers below are measured.

| step | result | time | model spend |
|---|---|---|---|
| Frame | pass | 15.9 s | 0.15 USD (Sonnet) |
| Plan | pass | 16.1 s | 0.17 USD (Sonnet) |
| Implement | pass (the developers' commit: 4 source files and 1 test file) | 0.06 s | none |
| Verify, round 1 | 6 tests written; revert check and lint passed; mutation wrongly failed (below) | writer 249 s | 1.88 USD (Opus) |
| Verify, round 2 | a repair round that could not pass; killed by the session while the writer ran | | not recorded |
| Verify, round 3 (after the factory fix) | 6 tests; every check passed; mutation recorded as not applicable; 6 readable cases | 7 min 31 s | writer 2.12 USD, cases 1.10 USD |
| Review | approve, two findings (medium, low) | 64 s | 0.27 USD |
| Ship | committed `59a58be` on `qa/isso-no-cache-comment-views`; isso's suite with the tests: 128 passed | 2.3 s | none |

Recorded spend 5.69 USD (`summary.md`), under the ticket's cap (raised from 6 to 10 USD before the
re-run). The killed round-2 call is not in `rounds.json`; the real total is higher by an amount
nobody measured.

**The tests (round 3).** 6 API tests, all passing with the change.
- **Old code:** 3 fail on an assertion (`[] != ['no-store']`): the thread listing, the listing with
  each query parameter, the single comment with and without `plain=1`. 3 pass on both versions,
  which the contract asks for (error responses and other routes get no header; bodies unchanged).
  They are regression guards, reported as such and not counted as proof.
- **Mutation: not applicable.** mutmut 3.8.0 generated 1039 mutants in `isso/views/comments.py`
  and none for the three changed functions (`no_cache_headers`, a decorator with an inner
  function; `API.view` and `API.fetch`, decorated). `set_no_cache_headers`, the function that sets
  the header, is in `isso/utils/__init__.py`, which the factory does not mutate. The developers'
  own tests reach no mutant either. The revert check is the only proof the tests exercise the
  change.
- **Review's findings, none blocking:** the "bodies unchanged" test checks some keys with
  `assertIn`, not the exact key set; the "other routes unchanged" test covers only the six routes
  the contract names.

**What the first attempt found in the factory.** Round 1's mutation check asked mutmut for the
three functions by name; mutmut aborted with "Filtered for specific mutants, but nothing matches"
(exit 1). The factory read that as "the generated tests never reach the changed functions", marked
it repairable and started a repair round that could not pass. The session killed the run during
that round, changed the check to record "no mutants" as not applicable
(`factory/checks/mutants.py`, `classify_exit`), and re-ran; the re-run started a fresh writer
(round 3), as a re-run after a failed Verify does. Round 1's tests, which were good (4 prove the
change, 2 guards), were not reused: `records/rounds.json` has both writers.

**Files here:** `report.md` (the QA evidence page), `summary.md` and `summary.json`, `tests/`
(the generated test file), `testcases/` (the six readable cases), `records/` (the step records,
`rounds.json`, and the Verify check reports of the final round).
