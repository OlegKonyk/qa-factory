"""The Ship step of the first path: the approved tests join the application's own suite.

In the head worktree a branch `qa/<ticket id>` is created from the change, the generated tests and
their readable cases are committed, and the application's suite runs once more with the new tests
in place. No pull request is opened yet: the application is not forked under Oleg's account
(docs/decisions.md). The commit in the worktree is the deliverable; its id is recorded.

Under the `person` mode it stops before anything is written to the worktree (gate `ship`): the
files, the branch and the suite that will run; `approve` commits and runs the suite, `decline` fails.
"""

import json
import os
import shutil
import subprocess
import time

from factory import gates
from factory.checks import suite

SHIP_ANSWERS = [
    {"decision": "approve", "means": "commit the tests and their cases on the branch and run the suite"},
    {"decision": "decline", "means": "nothing is committed; the step fails with the note as its reason"},
]


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


def restore_tests(head_tree: str, manifest_files: list[str], tests_dir: str | None) -> list[str]:
    """Put back any generated test missing from the head worktree, from the run folder's copy.

    Verify leaves the tests untracked in the ticket's head worktree and keeps a copy in the run
    folder. If the worktree was recreated (fetch.py after a wiped cache), the copy is the source.
    Returns the paths restored.
    """
    restored = []
    for rel in manifest_files:
        target = os.path.join(head_tree, rel)
        source = os.path.join(tests_dir, rel) if tests_dir else ""
        if not os.path.exists(target) and source and os.path.isfile(source):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
            restored.append(rel)
    return restored


def _cases(cases_dir) -> list[tuple[str, str]]:
    """(source, path under the application's root) for each readable case: they go under testcases/."""
    found = []
    if cases_dir and os.path.isdir(cases_dir):
        for area in os.listdir(cases_dir):
            src = os.path.join(cases_dir, area)
            if os.path.isdir(src):
                for name in os.listdir(src):
                    found.append((os.path.join(src, name), os.path.join("testcases", area, name)))
    return found


def _invocations(app, manifest_files):
    """The suite with the new tests in place: the recipe's first invocation (the API and unit tests),
    then the new browser files alone, when the recipe has a browser folder."""
    browser_dir = app.get("browser_tests_dir") or None
    browser_files = [p for p in manifest_files if browser_dir and p.startswith(browser_dir + "/")]
    invocations = [list(app["suite"][0])]
    if browser_files:
        invocations.append(["-o", f"python_files={app['browser_test_files']}", *browser_files])
    return invocations


def _ask(ticket, app, files, branch, invocations):
    return {
        "status": "needs_person",
        "artifacts": {},
        "reason": "ship mode is person: the commit waits for approval",
        "gate": {
            "kind": "ship",
            "who": gates.approver(app),
            "question": f"Commit {len(files)} files for '{ticket.get('title', ticket['id'])}' on {branch} "
            "and run the suite?",
            "context": {"files": files, "branch": branch, "suite": invocations},
            "answers": SHIP_ANSWERS,
        },
        "metrics": {},
    }


def run(inp):
    repo, ticket, artifacts, run_dir = (_field(inp, k) for k in ("repo", "ticket", "artifacts", "run_dir"))
    app, head_tree = repo["app"], repo["head_tree"]

    with open(artifacts["tests_manifest"]) as f:
        manifest = json.load(f)
    cases = _cases(artifacts.get("test_cases"))
    files = list(manifest["files"]) + [rel for _, rel in cases]
    branch = f"qa/{ticket['id']}"
    invocations = _invocations(app, manifest["files"])

    if "answer" in artifacts:
        answer = gates.read_answer(artifacts["answer"])  # the driver checked it against the gate
        if answer["decision"] != "approve":
            reason = f"ship declined by {answer['by']}: {answer.get('note', '')}".strip()
            return {"status": "fail", "artifacts": {}, "reason": reason, "gate": None, "metrics": {}}
    elif gates.mode_for("ship", ticket, app) == "person":
        return _ask(ticket, app, files, branch, invocations)

    out_dir = os.path.join(run_dir, "ship")
    os.makedirs(out_dir, exist_ok=True)
    restored = restore_tests(head_tree, list(manifest["files"]), artifacts.get("tests_dir"))
    for src, rel in cases:
        os.makedirs(os.path.dirname(os.path.join(head_tree, rel)), exist_ok=True)
        shutil.copy2(src, os.path.join(head_tree, rel))

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

    t0 = time.time()
    result = suite.run(head_tree, app["python"], invocations, app["pytest_args"])
    report = {
        "branch": branch,
        "commit": sha,
        "files": files,
        "restored_from_run_folder": restored,
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
