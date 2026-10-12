# Specs: track 2 build half, 2026-10-12 (cloud session)

Two independent pieces, built at the same time:

- `r1-report.md`: the run report, built by a subagent from this spec.
- The Restate service (`factory/restate_service.py`, the shared step runner in `factory/driver.py`)
  was built by the session itself; its shape is described in `docs/exploration.md`, "Track 2, the
  build half".

Oleg's plugins were not available in this cloud session, so the builder was a general-purpose
subagent given this spec, not a `supervisor:implementer`.
