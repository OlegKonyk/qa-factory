# Status

Read this first. Update it last, in the same pull request as the work.

**As of 2026-10-08.** The repository is prepared; no factory code exists yet. The next session is a
planning session with Oleg: he decides the open questions below, and the session after it builds
the first working path.

## Done

- The repository: `CLAUDE.md` (the product and the rules that keep it one), `docs/brief.md` (the
  requirements), `docs/inputs.md`, `docs/reference/lab.md` (the old lab and what may be
  salvaged), the commit guard in `hooks/`, `just setup` and `just check`.
- The old lab is closed and tagged `lab-end-2026-10-08` in `OlegKonyk/assay`.

## Open, for Oleg to decide in the planning session

Nothing here is decided. Each item says what it blocks.

1. **The test strategy**: the pyramid, the inverted pyramid, the honeycomb, or another shape, and
   how it is applied per change. Blocks the step that decides where new tests go.
2. **The first real application(s).** Both lab copies are public and already run here: linkding
   (Django, a REST API and a browser UI, 11 real features from 2026 with the developers' own
   tests) and isso (Python, SQLite, a small browser widget). An API-and-browser app is needed for
   both test kinds. Blocks everything that generates tests.
3. **Temporal on this machine.** The Temporal CLI is not installed here (checked 2026-10-08:
   `which temporal` finds nothing). Its local development server and the Python SDK are documented;
   not verified here. Blocks the orchestration.
4. **What a person approves**: human-readable test cases (Oleg's `signoff` plugin already writes
   them, `docs/reference/lab.md`), a Given/When/Then text, or something else; and where they
   approve it (a pull request, the tracker, a page). Blocks requirement 3.
5. **Which checks prove a test is not misleading, and in what order**: the test fails when its
   change is taken out, and for the right reason; mutmut on the changed code; the generated-test
   linter. Blocks requirement 2.
6. **How approved tests join the regression suite**: into the application's own test folders or a
   suite beside it, and how it stays fast and free of flaky tests. Blocks requirement 4.
7. **Which human gates of the backbone QA owns**: clarifying acceptance criteria, too many verify
   rounds, review sign-off.
8. **The first end-to-end path to build.** A candidate, for him to change: one real feature
   ticket goes into one Temporal workflow; Claude Code writes API and Playwright tests for it;
   the checks of item 5 run; readable test cases come out; a person approves; the tests are added
   to the suite.

## Next

1. The planning session (above).
2. Resolve the two links from the Temporal webinar slide, a repository and a blog post:
   `https://t.mp/4sdQ73H` (blog) and `https://t.mp/4?eqfa2` (repository; one character was hidden
   by the cursor in the photo). Not resolved.

## Waiting on Oleg

- His yes on this repository's `CLAUDE.md`, the first pull request.
- The planning session's answers.
- Whether the old lab's worktrees, and the four branches that exist only on this laptop, are kept
  or removed (`docs/reference/lab.md`).
