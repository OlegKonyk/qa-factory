# The next session

Paste one of these as the first message of the next session. Items 1 to 4 of `docs/roadmap.md`
were done on 2026-10-14 (`docs/log.md`); item 5 is next, item 6 after it. Each kickoff stands on
its own.

## Kickoff: the factory writes the change itself (roadmap item 5)

Start in ~/dev/qa-factory. Read CLAUDE.md, docs/roadmap.md item 5, docs/status.md and
docs/architecture.md, then `factory/steps/implement.py` and `factory/steps/verify.py` (the writer
loop, the caps, the stronger model, the gates of item 4). Build Implement as an agent step: a
fresh headless session (the same runner as the test writer, `factory/headless.py`) writes the
change test-first on a branch in the head worktree from the Frame and Plan artifacts, with the
ticket's `base` as the starting tree and no sight of the developers' commit or tests. Verify's
blind lane stays as it is and meets the agent's change on the deterministic checks (revert,
mutation, lint, suite, cases); a failing check goes back to Implement for a capped repair round,
then the stronger model, then a person through the Implement gate (`gates.implement`, the same
contract as the others). The check with a known answer: run it on the shipped tickets (linkding
sort and bundles, isso no-cache, gafaelfawr oidc-client-update), holding the developers' commit
and tests back from every session, and after the join run the developers' own tests against the
agent's change; record pass or fail per ticket as a deterministic check, not a score. Model calls
bill through `scripts/with-console-key.sh`; cap about 10 USD per ticket (estimated, nothing
measured yet), so run one ticket first and report its cost before the rest. Specs under
`docs/specs/`, Opus implementers in a workflow from written specs, an Opus reviewer per slice,
the session merges. Update `docs/adopt.md` in the same pull request (a ticket without `head`, the
new gate, the new caps), the item's State line, `docs/log.md`, `docs/decisions.md`,
`docs/status.md` last. Decisions that are Oleg's go to him as a numbered list at the end;
everything swappable is decided by delegation and recorded.

## Kickoff: ship as a pull request, approve on it (roadmap item 6)

Start in ~/dev/qa-factory. Read CLAUDE.md, docs/roadmap.md item 6, `factory/steps/ship.py`,
`factory/gates.py` and the Ship gate's section of `docs/adopt.md`. Build: Ship pushes the
`qa/<ticket id>` branch to a fork of the application on Oleg's GitHub account (the fork's remote
named in the recipe, `fork` in `app.json`, created by him or by `gh repo fork` under his login
with his say-so) and opens a pull request whose body holds the readable cases and the run report;
under `gates.ship: person` the pull request's approval (a review with "approve" by a named person)
is the answer, polled by the driver, and the answer file stays the fallback; the notification of
item 4 carries the pull request's link. Nothing is pushed anywhere unless the recipe names the
fork. Prove it on one shipped run (the gafaelfawr or linkding run folder, no model call needed:
`python -m factory redo <run> ship --rerun`), with the pull request opened on the fork and
approved by Oleg or by the session standing in, and say which. Update `docs/adopt.md` (the fork
field, the approval on the pull request, what the token needs: `gh auth status`), the State line,
`docs/log.md`, `docs/decisions.md`, `docs/status.md` last. The boundary stands: a fork of a public
application only; nothing of the employer's.
