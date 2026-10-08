# qa-factory

The QA part of an AI software factory, built as working code that runs on one machine. AI writes
the tests; deterministic tools check that they are not misleading; a person approves a readable
version; approved tests join the regression suite.

Start with `docs/status.md`. The rules are in `CLAUDE.md`, the requirements in `docs/brief.md`,
the decisions in `docs/decisions.md`.

```
just setup                                                      # once after cloning
just check                                                      # lint and the factory's tests
uv run python targets/linkding/fetch.py --ticket targets/linkding/tickets/sort-by-modified.json --prepare-e2e
uv run python -m factory run targets/linkding/tickets/sort-by-modified.json   # run or resume a ticket
uv run python -m factory status .artifacts/runs/linkding-sort-by-modified     # the step records
```

A run stops at a human gate with `question.md` in its run folder; an `answer.json` beside it
resumes the run.
