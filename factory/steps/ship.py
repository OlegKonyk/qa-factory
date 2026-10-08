"""The Ship step of the first path: the approved tests join the application's own suite.

In the head worktree a branch `qa/<ticket id>` is created from the change, the generated tests and
their readable cases are committed, and the application's suite runs once more with the new tests
in place. No pull request is opened yet: the application is not forked under Oleg's account
(docs/decisions.md). The commit in the worktree is the deliverable; its id is recorded.
"""

import json
import os
import shutil
import subprocess
import time

from factory.checks import suite


def _git(cwd, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL
    )
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])}: {p.stderr.strip()}")
    return p.stdout


def _field(inp, name):
    return getattr(inp, name) if hasattr(inp, name) else inp[name]


def run(inp):
    repo, ticket, artifacts, run_dir = (_field(inp, k) for k in ("repo", "ticket", "artifacts", "run_dir"))
    app, head_tree = repo["app"], repo["head_tree"]
    out_dir = os.path.join(run_dir, "ship")
    os.makedirs(out_dir, exist_ok=True)

    with open(artifacts["tests_manifest"]) as f:
        manifest = json.load(f)
    files = list(manifest["files"])

    # The readable cases travel with the tests, under testcases/ at the application's root.
    cases_dir = artifacts.get("test_cases")
    if cases_dir and os.path.isdir(cases_dir):
        dest = os.path.join(head_tree, "testcases")
        for area in os.listdir(cases_dir):
            src = os.path.join(cases_dir, area)
            if os.path.isdir(src):
                os.makedirs(os.path.join(dest, area), exist_ok=True)
                for name in os.listdir(src):
                    shutil.copy2(os.path.join(src, name), os.path.join(dest, area, name))
                    files.append(os.path.join("testcases", area, name))

    branch = f"qa/{ticket['id']}"
    existing = _git(head_tree, "branch", "--list", branch).strip()
    if existing:
        _git(head_tree, "checkout", "--quiet", branch)
    else:
        _git(head_tree, "checkout", "--quiet", "-b", branch)
    _git(head_tree, "add", "--", *files)
    _git(
        head_tree,
        "-c",
        "user.name=qa-factory",
        "-c",
        "user.email=qa-factory@localhost",
        "commit",
        "--quiet",
        "-m",
        f"Add QA tests for {ticket['title']}",
        "--allow-empty",
    )
    sha = _git(head_tree, "rev-parse", "HEAD").strip()

    # The suite with the new tests in place: the recipe's first invocation (the API and unit tests),
    # then the new browser files alone.
    browser_files = [p for p in manifest["files"] if p.startswith(app["browser_tests_dir"] + "/")]
    invocations = [list(app["suite"][0])]
    if browser_files:
        invocations.append(["-o", f"python_files={app['browser_test_files']}", *browser_files])
    t0 = time.time()
    result = suite.run(head_tree, app["python"], invocations, app["pytest_args"])
    report = {
        "branch": branch,
        "commit": sha,
        "files": files,
        "suite": result,
        "wall_s": round(time.time() - t0, 1),
    }
    path = os.path.join(out_dir, "report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=1)

    summaries = "; ".join(r.get("summary") or f"rc={r['returncode']}" for r in result["runs"])
    if result["status"] != "pass":
        return {
            "status": "fail",
            "artifacts": {"ship_report": path},
            "reason": f"suite red after merge: {summaries}",
            "gate": None,
            "metrics": {"wall_s": report["wall_s"]},
        }
    return {
        "status": "pass",
        "artifacts": {"ship_report": path},
        "reason": f"committed {sha[:7]} on {branch} in {head_tree}; suite green: {summaries}",
        "gate": None,
        "metrics": {"wall_s": report["wall_s"], "commit": sha},
    }
