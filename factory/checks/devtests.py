"""The revert check on the developers' own tests: do the tests written with the change prove it?

The same two-tree run as `factory/checks/revert.py` (every test runs with the change, then in a
copy where the changed source and the test helpers are put back to their old version), on the test
files the change itself added or modified, reported for the tests that are new at head (absent
from the file at base) or modified in place (same id, a different function, decorators included).
It never fails a run: it is the per-ticket answer, with a count, to "can
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


def _test_nodes(tree, relpath) -> dict[str, ast.AST]:
    """The test functions in a file by pytest id: file::Class::name for methods, file::name for functions."""
    nodes: dict[str, ast.AST] = {}
    try:
        module = ast.parse(Path(tree, relpath).read_text())
    except (OSError, SyntaxError):
        return nodes
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith("test"):
                    nodes[f"{relpath}::{node.name}::{item.name}"] = item
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            nodes[f"{relpath}::{node.name}"] = node
    return nodes


def test_ids(tree, relpath) -> list[str]:
    """Pytest ids of the tests in a file: file::Class::name for methods, file::name for functions."""
    return list(_test_nodes(tree, relpath))


def judged_test_ids(head_tree, base_tree, relpath, status) -> dict[str, str]:
    """The tests in `relpath` at head the change wrote: id -> "new" (absent at base) or "modified".

    Modified means the file had a test of that id at base with a different function (its AST
    without positions, decorators included). Unchanged tests are left out; a renamed test is new.
    """
    head = _test_nodes(head_tree, relpath)
    base = _test_nodes(base_tree, relpath) if status == "M" else {}
    kinds: dict[str, str] = {}
    for test_id, node in head.items():
        if test_id not in base:
            kinds[test_id] = "new"
        elif ast.dump(node, include_attributes=False) != ast.dump(base[test_id], include_attributes=False):
            kinds[test_id] = "modified"
    return kinds


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
    """Run the revert check on the developers' new and modified tests and count the verdicts. Never raises."""
    support = set(test_support or ())
    kinds: dict[str, str] = {}
    files: set[str] = set()
    for row in changed_tests:
        path = row["path"]
        if row["status"] not in ("M", "A") or not path.endswith(".py") or path in support:
            continue
        judged = judged_test_ids(head_tree, base_tree, path, row["status"])
        if judged:
            files.add(path)
            kinds.update(judged)
    if not kinds:
        return {
            "status": "skipped",
            "reason": "the change added or modified no test",
            "files": [],
            "new_test_ids": {},
            "kinds": {},
            "tests": {},
            "counts": {"new_tests": 0, "modified_tests": 0, "ran": 0, **dict.fromkeys(VERDICTS, 0)},
        }
    new: dict[str, list[str]] = {}
    for test_id, kind in kinds.items():
        if kind == "new":
            new.setdefault(test_id.partition("::")[0], []).append(test_id)
    report = revert.run(
        head_tree,
        base_tree,
        changed_source,
        sorted(files),
        workdir,
        python,
        pytest_args,
        list(test_support or ()),
        browser_glob,
        exclude_copy,
        timeout,
    )
    tests = {k: v for k, v in (report.get("tests") or {}).items() if k in kinds}
    counts = {
        "new_tests": sum(k == "new" for k in kinds.values()),
        "modified_tests": sum(k == "modified" for k in kinds.values()),
        "ran": len(tests),
    }
    for verdict in VERDICTS:
        counts[verdict] = sum(t.get("verdict") == verdict for t in tests.values())
    if tests:
        status = "ran"
        ran_new = sum(kinds[t] == "new" for t in tests)
        reason = (
            f"{counts['proves-behaviour']} of {len(tests)} tests by the developers "
            f"({ran_new} new, {len(tests) - ran_new} modified) fail on the old code "
            f"on an assertion; {counts['missing-name']} fail only for a missing name"
        )
    else:
        status, reason = "error", report.get("reason") or "the revert check gave no result"
    return {
        "status": status,
        "reason": reason,
        "files": sorted(files),
        "new_test_ids": new,
        "kinds": {t: kinds[t] for t in sorted(kinds)},
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
        kind = (result.get("kinds") or {}).get(node, "new")
        out.write(f"  {t.get('verdict'):<22} {kind:<8} {node}\n")
    return 0 if result["status"] != "error" else 1
