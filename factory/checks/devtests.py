"""The revert check on the developers' own tests: do the tests written with the change prove it?

The same two-tree run as `factory/checks/revert.py` (every test runs with the change, then in a
copy where the changed source and the test helpers are put back to their old version), on the test
files the change itself added or modified, reported for the tests that are new at head (absent
from the file at base). It never fails a run: it is the per-ticket answer, with a count, to "can
the tests written in the session that implemented the change be trusted" (`docs/trust.md`).

`python -m factory devtests <run folder>` runs it alone on a finished run, with no model call,
from the Implement step's record and the ticket's worktrees.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

from factory.checks import revert

VERDICTS = ("proves-behaviour", "passes-without-change", "missing-name", "crash", "head-fails", "skip")


def test_ids(tree, relpath) -> list[str]:
    """Pytest ids of the tests in a file: file::Class::name for methods, file::name for functions."""
    ids: list[str] = []
    try:
        module = ast.parse(Path(tree, relpath).read_text())
    except (OSError, SyntaxError):
        return ids
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith("test"):
                    ids.append(f"{relpath}::{node.name}::{item.name}")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            ids.append(f"{relpath}::{node.name}")
    return ids


def new_test_ids(head_tree, base_tree, relpath, status) -> list[str]:
    """The tests in `relpath` at head that the file did not have at base (all of them for a new file)."""
    head = test_ids(head_tree, relpath)
    base = set(test_ids(base_tree, relpath)) if status == "M" else set()
    return [t for t in head if t not in base]


def run(
    head_tree,
    base_tree,
    changed_source,
    changed_tests,
    workdir,
    python,
    pytest_args,
    test_support,
    browser_glob,
    exclude_copy,
    timeout=900,
) -> dict:
    """Run the revert check on the developers' new tests and count the verdicts. Never raises."""
    support = set(test_support or ())
    new: dict[str, list[str]] = {}
    for row in changed_tests:
        path = row["path"]
        if row["status"] not in ("M", "A") or not path.endswith(".py") or path in support:
            continue
        ids = new_test_ids(head_tree, base_tree, path, row["status"])
        if ids:
            new[path] = ids
    if not new:
        return {
            "status": "skipped",
            "reason": "the change added no test",
            "files": [],
            "new_test_ids": {},
            "tests": {},
            "counts": {"new_tests": 0, "ran": 0, **dict.fromkeys(VERDICTS, 0)},
        }
    report = revert.run(
        head_tree,
        base_tree,
        changed_source,
        sorted(new),
        workdir,
        python,
        pytest_args,
        list(test_support or ()),
        browser_glob,
        exclude_copy,
        timeout,
    )
    wanted = {i for ids in new.values() for i in ids}
    tests = {k: v for k, v in (report.get("tests") or {}).items() if k in wanted}
    counts = {"new_tests": len(wanted), "ran": len(tests)}
    for verdict in VERDICTS:
        counts[verdict] = sum(t.get("verdict") == verdict for t in tests.values())
    if tests:
        status = "ran"
        reason = (
            f"{counts['proves-behaviour']} of {len(tests)} new tests by the developers fail on the old code "
            f"on an assertion; {counts['missing-name']} fail only for a missing name"
        )
    else:
        status, reason = "error", report.get("reason") or "the revert check gave no result"
    return {
        "status": status,
        "reason": reason,
        "files": sorted(new),
        "new_test_ids": new,
        "tests": tests,
        "counts": counts,
        "wall_s": report.get("wall_s"),
    }


def run_on_record(run_dir) -> dict:
    """Run the check from a finished run's Implement record; writes verify/developers_revert.json."""
    folder = Path(run_dir)
    record = json.loads((folder / "steps" / "03-implement.json").read_text())
    repo, artifacts = record["input"]["repo"], record["output"]["artifacts"]
    if not os.path.isdir(repo["head_tree"]):  # a record older than the per-ticket worktrees (2026-10-10)
        from factory import driver

        ticket = record["input"]["ticket"]
        if (folder / "ticket.json").is_file():
            ticket = json.loads((folder / "ticket.json").read_text())
        repo = driver._load_repo(ticket)
    app = repo["app"]
    with open(artifacts["changed_source"]) as f:
        changed_source = json.load(f)
    with open(artifacts["changed_tests"]) as f:
        changed_tests = json.load(f)
    out = folder / "verify"
    out.mkdir(parents=True, exist_ok=True)
    result = run(
        repo["head_tree"],
        repo["base_tree"],
        changed_source,
        changed_tests,
        str((out / "developers_revert").resolve()),  # the pytest plugin writes relative to the tree
        app["python"],
        app["pytest_args"],
        app["test_support"],
        app.get("browser_test_files") if app.get("browser_tests_dir") else None,
        app["exclude_copy"],
    )
    entry = {"status": "pass", "result": result}
    with open(out / "developers_revert.json", "w") as f:
        json.dump(entry, f, indent=1, default=str)
    return result


def main(run_dir: str, out=None) -> int:
    out = out or sys.stdout
    if not os.path.isfile(os.path.join(run_dir, "steps", "03-implement.json")):
        (out if out is not sys.stdout else sys.stderr).write(f"no Implement record under {run_dir}\n")
        return 2
    result = run_on_record(run_dir)
    out.write(f"{result['status']}: {result['reason']}\n")
    for node, t in result["tests"].items():
        out.write(f"  {t.get('verdict'):<22} {node}\n")
    return 0 if result["status"] != "error" else 1
