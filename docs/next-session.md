# The next session

Paste this as the first message of the next session. Items 1, 2 and 4 of `docs/roadmap.md` were
done on 2026-10-14 (`docs/log.md`); item 3 is next. Kickoffs for items 5 and 6 are written when
item 3 is done.

## Kickoff: a third application shaped like a small team service (roadmap item 3)

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/adopt.md. That guide is the whole procedure
(its section 3 now starts with the checklist score and the application's agent file);
docs/status.md says what exists and docs/trust.md what the factory claims. Onboard <application>
by following docs/adopt.md and nothing else, through all eight items of its checklist (section 8),
with the model calls billed through `scripts/with-console-key.sh` on this laptop (elsewhere,
`ANTHROPIC_API_KEY`). Cap: one ticket, about 6 USD (estimate). Fold every place the guide was wrong
or silent back into docs/adopt.md in the same pull request. A branch per change, `just check`
green, a squash PR with the output in the body, a docs/log.md entry, the item's State line in
docs/roadmap.md, docs/status.md updated last.

Pointing the factory at a work repository is Oleg's call (CLAUDE.md, boundary). If the application
is his, he says so in this prompt; otherwise pick a public one with the shape of roadmap item 3:
a web API service (FastAPI or similar), a `src/` layout, a database run in Docker, and at least
one outside HTTP service it calls. Its ticket is a bug fix from the application's own history,
written blind. The outside service is mocked inside the application's suite; build mock machinery
only if this run needs it, and record what keeping the mock reliable took. If the application
has browser tests, give the writer's session the Playwright CLI (`@playwright/cli`) for exploring
the running app and record the writer's tokens and cost against the bundles run (3.62 USD),
as `docs/research/2026-10-14-agent-friendly-repositories.md` asks; adopt or drop on that number.
Oleg's answers of 2026-10-14 apply: a public application, chosen here.

What changed in the factory on 2026-10-14 that an onboarding agent meets (all in `docs/adopt.md`):
`gates.<step>` in the recipe or the ticket (`auto`, `model`, `person`); Frame stops the run when a
criterion cannot be made checkable or the ticket leaves out the public contract, and the answer
may carry the clarified ticket; a stopped run is listed by `python -m factory waiting`; the
answer file needs `by`; decorated functions and `__init__.py` get mutants now, and
`python -m factory mutation <run folder>` re-runs that check with no model call; a spend cap hit
after the checks resumes at the readable cases once `caps.usd` is raised. The deployed-instance
suite (`targets/linkding/deployed/`, section 10 of the guide) is the shape to copy if the third
application is to be run against its container too; that is optional for this kickoff.
