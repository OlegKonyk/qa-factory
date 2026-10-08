# qa-factory

This repository builds the QA part of an AI software factory as working code. A ticket goes in,
agents frame, plan, implement, verify, review and ship the change, and people approve at set
gates. The factory runs on this machine, on Temporal. The first part built is QA: generate API
and Playwright tests, prove they are not misleading, show a person something readable to approve,
and add the approved tests to the regression suite where the test strategy says coverage belongs.
`docs/brief.md` has the requirements. `docs/status.md` has where things stand.

**The output is software that runs.** It is not a recommendation, a comparison or a report.

## Rules that keep it a product

These exist because the first attempt, a separate lab, spent three days measuring and produced no
useful code. `docs/reference/lab.md` has the story and what can be salvaged.

1. **AI writes the tests and the code. Deterministic tools check them:** mutation testing
   (mutmut), coverage, the check that a new test fails when its change is taken out, linters, the
   app's own suites. No non-AI test generators (Pynguin, EvoSuite and the like), not even as a
   baseline.
2. **No bake-offs.** Do not evaluate, compare or score tools unless Oleg asks for that comparison by
   name. Pick the obvious current tool, use it, and replace it if it fails in use.
3. **One working path first.** Before building supporting machinery (sandboxes, ledgers, scorers,
   harnesses, dashboards), one end-to-end path has to produce a real test on a real application.
   Machinery is added when a run shows it is needed, not before.
4. **Every session ends with factory code that runs,** shown by the command and its output, or
   says plainly why it does not. A plan, research or a document is never a session's only output
   unless Oleg asked for exactly that.
5. **Research is short and serves the next build step.** Answer the question that blocks building,
   label each claim checked, documentation only, or not verified, and stop.
6. **No stand-in apps and no planted bugs to score the factory.** The factory runs on real
   applications. A test's strength is measured with mutation testing on real code.
7. **Parallel agents build independent pieces from a written spec.** Never fan out agents to
   evaluate, review in rounds, or research for its own sake.
8. **Decisions are Oleg's.** Open questions go to him as questions with a recommendation. A
   session does not settle the test strategy, the target applications or the factory's shape on
   its own.

## Evidence

Show the command and its output. A number is labelled measured or estimated. A skipped step is
stated as skipped. Nothing is called working until it has run here.

## Working with Oleg

- He gives direction in dictated brain dumps; expect transcription slips. File each input in
  `docs/inputs.md`, with your reading of it, before working on it.
- He does not do git chores. Carry work end to end within these rules.
- Reports to him are plain English for a person reading cold: what was done, what it showed, what
  is his to decide. No coined project vocabulary at all, not even defined. Show the tools and
  techniques under the hood by name and version.
- He wants speed and visible progress on real code.

## Boundary: not negotiable

This repository is on a personal GitHub account. Private is not the same as the employer's.

- Nothing that identifies the employer is ever committed, pushed, or written into an issue or PR:
  no company, product or partner names, no codenames, no service names, no domains or internal
  URLs, no screenshots, no credentials.
- Raw hand-offs, photos and every employer-specific note live in `.local/`, which is gitignored.
  What enters the repository is the generic derivative.
- The factory runs against public applications on this machine. Pointing it at a work environment
  is Oleg's call, never a session's.
- `hooks/guard.sh` blocks commits containing terms from a local list outside the repository. It is
  the backstop, not the rule. Never print or copy that list.

## Mode: rapid

- No hosted CI; GitHub Actions is disabled on the repository. `just check` is the definition of
  green and grows with the code.
- Branch per change (`<type>/<slug>`), never commit to `main`. Merge by squash PR once `just check`
  is green and its output is in the PR body. A session may merge its own PR on that basis. A PR
  that changes this file or `hooks/` waits for Oleg.

## The old lab

`~/dev/assay` (GitHub `OlegKonyk/assay`, tag `lab-end-2026-10-08`) is read-only history. Read
`docs/reference/lab.md` before touching it. Copy a piece from it only when the factory needs that
piece now. Never resume its plans, its experiments or its vocabulary.

## Commands

`just setup` wires the hooks. `just check` runs the checks.
