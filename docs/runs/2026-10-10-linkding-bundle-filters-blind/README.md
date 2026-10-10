# The bundles ticket, written blind (2026-10-10)

`uv run python -m factory run targets/linkding/tickets/bundle-filters-blind.json`, three times:

1. Frame, Plan, Implement, then Verify round 1: 13 blind tests, all passing with the change, all
   counted "missing name" on the old code. The cause was the factory's revert check (the developers'
   new test helper on the old code). Round 2, the repair round, worked around it and was failed for a
   `package-lock.json` change the preparation had made. Fable 5.1 ran out of budget, so the run
   stopped for a person (`records/question.md`). 834 s wall.
2. Run on the old code by mistake with no answer; nothing changed (0.08 s).
3. After pull request 14, the session answered `recheck` for round 1
   (`records/steps/04-verify.answer1.json`, Oleg not asked): round 3 judged the same round-1 tests
   with the fixed checks and passed lint, revert, mutation and the suite. The step then stopped at
   the ticket's 8 USD cap, before the readable cases. 312 s wall, no model spend.

- `tests/`: the round-1 tests, as written blind.
- `records/verify/rounds/<n>/`: each round's check reports and tests; `records/verify/escalation-1.json`
  the stronger model's call; `records/rounds.json` every model call of the ticket.
- `summary.md`: the numbers (`python -m factory summary`).
