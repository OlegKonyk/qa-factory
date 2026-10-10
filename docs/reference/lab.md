# The old lab: what it was, why it produced no useful code, what may be salvaged

`~/dev/assay`, GitHub `OlegKonyk/assay`, final state tagged `lab-end-2026-10-08` (commit
`c8eb60a`). Read-only history. Paths below are inside that repository at that tag unless a branch
is named. Copy a piece only when the factory needs it now; never resume the lab's plans.

## What it was

Three days (2026-10-06 to 2026-10-08) of a repository whose instruction file opened with "A lab
for one decision [...] The output is a recommendation, not a product." It built prototypes only to
compare them: stand-in apps it wrote itself with bugs it planted, a scorecard, experiments with
control groups, adopt-or-drop rules written before each run. Its last plan (trialling test-writing
tools on two real open-source apps) built about 12,700 lines of supporting code across seven
pieces and generated no test before it was stopped.

## Why it produced no useful code

- **The kickoff was misread.** "A set of prototypes to see what is possible [...] a handful of
  distinct solutions to touch them, feel them, and make a decision" was written down as "the output
  is a recommendation, not a product". Every session read that line first.
- **"A script decides pass or fail" was stretched to "keep AI out".** The work became checks and
  graders, with almost no AI writing tests.
- **Measuring needed known bugs, so it wrote fake apps and planted them.** Counting planted bugs
  caught rewards tests of code that already exists, so three days produced regression results,
  not new coverage.
- **"Predictable tools" was heard as "tools without AI"**, which brought in Pynguin.
- **Each pushback added rigor instead of changing direction**: pre-registered rules, sandboxes,
  reviewer rounds, more machinery before any tool had run.

## Salvage candidates

Not decided; listed so the planning session can choose. "Measured" numbers were measured in the
lab, mostly on its own stand-in apps, and do not carry over as facts about real code.

| Piece | What it does | Where | State | Possible use |
|---|---|---|---|---|
| Mutation wrapper | Wraps mutmut 3.8.0: mutates only the functions a change touched, runs each mutant on a fresh copy, reports which tests kill which mutants | branch `feat/coverage-mutants`, `scripts/coverage/mutants.py` | 49 unit tests pass; never second-reviewed. Measured on isso commit 124a923: the developers' tests killed 91 of 119 mutants | "Are these tests misleading?" on changed code |
| Revert check and empty-test lint | For any git repo tested with pytest: a new test must fail when its change is taken out; flags tests that assert nothing | `scripts/grader/` | On main, its own checks green | The core "not misleading" gate |
| Generated-test linter | Flags bad habits in generated tests: reaching into private names, mocking the app's own internals, sleeps, comparisons against a large pasted literal, duplicates of existing tests | branch `feat/coverage-lint`, `scripts/coverage/lint.py` | 52 unit tests pass; never second-reviewed | A cheap gate before mutation |
| Fail-before sorter | Sorts why a new test fails on the old code: a missing name, a crash before any check, or a real failed check. Only the last proves the test checks behaviour | branch `feat/coverage-failsort` (this laptop only) | 68 unit tests, 1 failing, fix unfinished. Measured: in 3 of 4 recent isso features, the developers' own new tests failed the old code without any behaviour check running | Makes the revert check honest |
| Sandbox for agent-written code | macOS `sandbox-exec` profile: agent-written tests run with no network and writes only inside their run folder | branch `feat/coverage-confine` (this laptop only); probe in `docs/findings/new-coverage/probes.md` | 34 unit tests, 2 failing, fix unfinished. The probe measured it works with isso's suite and mutmut | Running generated tests safely, if needed |
| Safe file access | Reads and writes that refuse symlinks, hard links and paths outside a folder | `scripts/coverage/safefs.py` | On main, tests pass | Small; copy with the sandbox |
| Verdict file | One JSON pass/fail document per test run, from JUnit XML or vitest JSON; refuses an empty or all-skipped run | `scripts/verdict/` | On main, checks green | The verify step's output record |
| Headless agent runner | Drives Claude Code headless through phases on one ticket and records a run folder; a fresh-context verifier must hand over a runnable check per criterion | `scripts/harness/`, `scripts/x3/`, finding `docs/findings/x3-fresh-context.md` | On main. Measured on a stand-in app: required to hand over a runnable check, both verifiers caught a slipped-in regression 6 of 6 times | Shape of the agent steps; Temporal would replace the driver |
| Test from a ticket | An agent writes a reproducing test from the ticket text alone | `scripts/authoring/` (`repro` mode), finding `docs/findings/authoring-and-regression.md` | Measured on a stand-in app: 19 of 20 valid, $0.11 a run | First QA step for a bug ticket |
| Feature descriptions | Builds each isso feature's description from its commit message and linked issues, cut at the date the feature landed | branch `feat/coverage-material`, `scripts/coverage/material.py` | 50 unit tests pass; never second-reviewed | Input for tests written from a feature description |
| isso | Open-source comment server (Python, SQLite), copied unchanged at 0.14.0, 113 tests in about 3 s | `targets/isso/` (the clean copy; ignore `targets/keys/`) | Measured runnable, browser bundle builds | A real app for the factory to work on |
| linkding | Open-source bookmark manager (Django, REST API, browser UI), fetched by a script, 11 real 2026 features with the developers' own tests | branch `feat/coverage-material`, `targets/linkding/` | Measured: one setup runs all 11 features' tests, all pass | A real app with API and Playwright surfaces |
| Setup facts | Measured: mutmut on isso, isso's browser build and tests, Playwright's browsers, Spec Kit run headless, linkding's history, the sandbox | `docs/findings/new-coverage/probes.md` | On main | Saves re-discovering setup traps |
| Flaky-test sorter | Classes tests as flaky from randomised repeat runs, keeps a quarantine file with owner and reason | `candidates/quarantine-by-rerun/` | On main. Measured on a stand-in: 3 of 3 planted flakes classed | Regression-suite hygiene |
| Test selection | Runs only the tests a change can affect (pytest-testmon), the whole suite on anything unclear | `candidates/select-by-impact/` | On main | Keeping the regression suite fast |
| Human-readable test cases and risk-ranked gaps | Oleg's own `signoff` plugin: writes test cases a person reads (`testcases/<area>/TC-*.md`), maps what the app does to what the tests cover, ranks the gaps by risk | `~/dev/konyklabs/claude-plugins/plugins/signoff/`; used once in the lab, `targets/permitdesk/testcases/coverage.md` | Used once: 43 behaviours found, 22 uncovered, 7 of those high risk (measured, stand-in app). Known gap: "covered" trusts a hand-written marker on each test | Requirements 3 and 5 of the brief |
| Tool scans | Landscape scans of test-writing tools, regression tooling and factory UIs, each claim labelled | `docs/research/2026-10-06-*.md`, `2026-10-07-deterministic-layers.md` | Written for comparison; may be stale | Skim for names only |

Four lab branches exist on this laptop only, because they fail their own fast tests and the push
check refuses them: the two marked above, `feat/coverage-agent` (a Claude Code launcher with
spend caps and test-file capture, 28 unit tests, 2 failing and 2 errors) and `feat/coverage-envs`.
They live in the lab's worktrees under `~/dev/assay/.claude/worktrees/`. Removing those worktrees
loses them; that is Oleg's call.

## Salvaged so far, and what is still to take (2026-10-10)

The lab is kept as it is: read-only history, nothing deleted (Oleg, 2026-10-10). Pieces are taken
when the factory needs them. Taken so far, all in the first path:

| From the lab | Where it went |
|---|---|
| The linkding fetch script, its cached clone and its list of 2026 features | `targets/linkding/fetch.py` (rewritten); the clone served as the mirror; the feature for the first ticket came from the list |
| The linkding history probe: which features' own tests fail on the old code, and why | Chose the first feature (its developers' tests fail only on a missing name), and is the evidence behind the loop recommendation in `docs/exploration.md` |
| The mutmut probe: one fresh copy per run, function-scoped globs, never reuse the cache, the `.meta` exit codes, the mangled names | `factory/checks/mutants.py` |
| The revert check's two-tree construction (base source under head tests) | `factory/checks/revert.py` |
| The fail-before sorter's pytest plugin | `factory/checks/failsort_plugin.py`, rewritten, with two fixes the lab had not found (assertions in helpers and in Playwright's `expect`, and unittest failures arriving without frames) |
| The headless runner's measured flags (no `$schema` in `--json-schema`, permission flags) | `factory/headless.py` |

Next to take, as the tracks reach them: "test from a ticket" (track 1 runs that idea on real code);
the feature-description builder for writing tickets from commits and issues; the sandbox for
agent-written tests; the flaky-test sorter and test selection by impact, when the suite needs
them; the generated-test linter's extra rules (private names, large pasted literals, duplicates);
isso as the second application.

## Not worth salvaging

- **Pynguin**, its environments (branch `feat/coverage-envs`) and every other non-AI generator.
- **The scorecard, the candidate cards, the pre-registered rules**, and every result of the form
  "N of 10 planted bugs caught".
- **The stand-in apps and planted bugs** (`targets/permitdesk`, `targets/ledgerbook`,
  `targets/keys/`), as anything to score the factory against.
- **The AI-drafted rules list for isso** waiting for a person's line-by-line approval, and the
  measurement built around it.
- **The lab's vocabulary.** None of its coined terms carry over.
