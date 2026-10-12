# Restate on the laptop (2026-10-12)

Restate 1.7.13 was installed on macOS with `brew install restatedev/tap/restate-server restatedev/tap/restate`. The server runs with `restate-server --base-dir ~/Library/Caches/qa-factory/restate`, its UI at http://localhost:9070. All numbers are measured.

**The stand-in proof again, on the laptop, with no model calls.**

- **One stand-in ticket end to end:** `run docs/runs/2026-10-12-restate-stub/ticket.json --engine restate --key stub-laptop-1`. It parked at the gate, was answered over HTTP and finished.
- **A hard kill mid-step, on a second stand-in run** (`stub-laptop-2`): `pkill -9` of the service 4 s into the 40 s Verify, then a restart. The call log is `stub-laptop-2-calls.log`. Frame, Plan and Implement each started once, in the first process. Verify started again in the new process, and the run then parked at the gate. This matches the cloud result.
- **A plain `kill` (SIGTERM) does not stop the service.** The first attempt used `pkill` without `-9`. The step in flight finished, and the old process was still listening on its port minutes later, so the restarted service failed with "Address already in use". Stop the service with `kill -9`. The cloud session saw the same thing.

**What the UI shows.**

- `ui-list-parked-at-gate.png`: in the invocations list, a run parked at the person-gate shows as **Running**, the same as a run that is working. That is because the 30-minute inactivity timeout keeps it attached to the service. The list does not say that a person is needed.
- `ui-journal-parked-at-gate.png` (the stand-in) and `ui-journal-real-parked-at-gate.png` (the real bundles ticket): the run's own page shows the journal. Each step is a `run("0N-name")` entry with its duration, and the open gate is `promise("verify-1")`, with the time spent waiting on it.
- `ui-journal-real-verify-running.png`: the real ticket 52 s in, with Verify running.

**`just check` with `restate-server` installed:** 213 passed, 1 skipped (the slow mutation test). The live Restate test now runs.
