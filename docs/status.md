# Status

Read this first. Update it last, in the same pull request as the work.

**As of 2026-10-08, after the planning session.** The repository is prepared and the plan is
decided; no factory code exists yet. The next session builds the first end-to-end path
(`docs/next-session.md` is the prompt for it).

## Done

- The repository: `CLAUDE.md`, `docs/brief.md`, `docs/inputs.md`, `docs/reference/lab.md`, the
  commit guard in `hooks/`, `just setup` and `just check`.
- The old lab is closed and tagged `lab-end-2026-10-08` in `OlegKonyk/assay`.
- The planning session (2026-10-08): the two Temporal links resolved (the Temporal Agent Harness,
  `temporal-community/temporal-agent-harness` 0.6.0, and its announcement post), the harness read
  from source and not run, and `docs/decisions.md` written: Temporal deferred until the loop runs;
  the ten planning questions decided by delegation. The review page Oleg used is a private
  artifact; its substance is in `docs/decisions.md`.

## Decided

`docs/decisions.md`. In one paragraph: a plain Python driver runs the seven steps of the backbone
over one run folder per ticket, stops when a step needs a person and resumes from the answer. The
step contract is one input envelope and one output envelope with artifacts as files. Verify is
the QA step and is built fully: Claude Code headless writes pytest API and Playwright tests; lint,
the revert check with its failure sorter, mutmut on the changed functions and the application's
own suite check them in that order; readable test cases in the signoff format are approved on the
pull request; approved tests join the application's own suite where the per-application strategy
rule says. The other steps are simplified but real. linkding first, isso second.

## Next

1. The first build session, from `docs/next-session.md`: the first path on linkding.
2. After the loop runs: the agent-written Implement step, the Learn step, flaky quarantine and
   test selection, and whether Temporal goes under the driver.

## Waiting on Oleg

- Whether the factory at work is built on Temporal. Decides the Temporal question later; blocks
  nothing now.
- Whether the old lab's worktrees, and the four branches that exist only on this laptop, are kept
  or removed (`docs/reference/lab.md`).
