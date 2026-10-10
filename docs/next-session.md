# The next session: close the first run, then the second ticket

Paste this as the first message of the next session.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md, docs/log.md and docs/decisions.md. The first
path exists and runs (`docs/status.md`, "Done"); do not rebuild it.

1. If `.artifacts/runs/linkding-sort-by-modified/answer.json` exists, run
   `uv run python -m factory run targets/linkding/tickets/sort-by-modified.json` and report what
   Review and Ship did. If it does not exist, the gate is still Oleg's; leave it and go on.
2. Write the second ticket from linkding commit 573b6f5 ("Filter bundles by reading or sharing
   state", base is its parent) into `targets/linkding/tickets/`, run
   `uv run python targets/linkding/fetch.py --ticket <that ticket> --prepare-e2e`, and run the
   factory on it to the gate. Each ticket has its own worktrees, so the first run stays parked
   untouched. Fix what breaks in the factory, not in the application. Record the
   numbers (spend per step, time per check, mutation scores) in `docs/runs/`.
3. Carry the second run's lessons into the prompts and checks, with a test for each change.

Build with Oleg's plugins as `CLAUDE.md` says; the supervisor skills need him to arm them
(`docs/plugin-notes.md`), so spawn its agents directly with written specs when he has not.
Branch per change, `just check` green, squash PR with the output in the body, a `docs/log.md`
entry and `docs/status.md` last, report in plain English.
