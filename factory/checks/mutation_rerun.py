"""Run Verify's mutation check again on a finished run, with no model call.

`python -m factory mutation <run folder>` reads the Implement record and the run's
`verify/tests_manifest.json`, puts the shipped tests back into the head worktree from
`verify/tests/` when they are missing, and runs `verify.run_mutation` (the same check Verify runs)
with its mutated copies under `verify/mutation-rerun/`. The result goes to
`verify/mutation-rerun.json`; Verify's own `verify/mutation.json` is never touched.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _input(folder: Path) -> dict:
    """The step input Verify got, rebuilt from the Implement record."""
    record = json.loads((folder / "steps" / "03-implement.json").read_text())
    repo, ticket = record["input"]["repo"], record["input"]["ticket"]
    if not os.path.isdir(repo["head_tree"]):  # a record older than the per-ticket worktrees (2026-10-10)
        from factory import driver

        if (folder / "ticket.json").is_file():
            ticket = json.loads((folder / "ticket.json").read_text())
        repo = driver._load_repo(ticket)
    return {
        "repo": repo,
        "ticket": ticket,
        "artifacts": record["output"]["artifacts"],
        "run_dir": str(folder),
    }


def run_on_record(run_dir) -> dict:
    """The mutation check on a finished run; writes and returns {status, reason, result}."""
    from factory.steps import verify
    from factory.steps.ship import restore_tests

    folder = Path(run_dir).resolve()
    ctx = verify._context(_input(folder))
    ctx["out"] = str(folder / "verify" / "mutation-rerun")  # the mutated copies; Verify's stay as they were
    manifest = json.loads((folder / "verify" / "tests_manifest.json").read_text())
    ctx["files"] = list(manifest["files"])
    restored = restore_tests(ctx["head_tree"], ctx["files"], str(folder / "verify" / "tests"))
    try:
        report = verify.run_mutation(ctx)
        entry = {"status": "pass", "reason": report.get("skipped") or "mutmut ran", "result": report}
    except verify.CheckFailed as e:
        # repairable: mutmut ran and the tests fell short; not repairable: mutmut itself did not run
        entry = {"status": "fail" if e.repairable else "error", "reason": str(e), "result": e.report}
    entry["restored_tests"] = restored
    entry["timings"] = ctx["timings"]
    with open(folder / "verify" / "mutation-rerun.json", "w") as f:
        json.dump(entry, f, indent=1, default=str)
    return entry


def _score(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def main(run_dir: str, out=None) -> int:
    out = out or sys.stdout
    err = out if out is not sys.stdout else sys.stderr
    if not os.path.isfile(os.path.join(run_dir, "steps", "03-implement.json")):
        err.write(f"no Implement record under {run_dir}\n")
        return 1
    try:
        entry = run_on_record(run_dir)
    except Exception as e:  # any failure of the command is exit 1, with its message
        err.write(f"error: {type(e).__name__}: {e}\n")
        return 1
    report = entry.get("result") or {}
    for name, r in (report.get("runs") or {}).items():
        changed = r.get("on_changed_lines") or {}
        out.write(
            f"{name}: checked {r.get('checked')}, killed {r.get('killed')}, survived {r.get('survived')}, "
            f"score {_score(r.get('score'))}; on the changed lines: checked {changed.get('checked')}, "
            f"killed {changed.get('killed')}, survived {changed.get('survived')}, "
            f"score {_score(changed.get('score'))}\n"
        )
    first = next(iter((report.get("runs") or {}).values()), {})
    if report.get("skipped"):
        out.write(f"skipped: {report['skipped']}\n")
    else:
        for glob in first.get("unmutated") or []:
            out.write(f"skipped: mutmut made no mutant for {glob}\n")
    if entry["status"] != "pass":
        out.write(f"{entry['status']}: {entry['reason']}\n")
    return 1 if entry["status"] == "error" else 0
