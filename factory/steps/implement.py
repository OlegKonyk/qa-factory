"""The Implement step of the first path: the developers' real commit is the change.

The ticket names a base and a head commit of the application. This step checks the two worktrees
out at those commits, makes sure the application's data folders exist, and records the change as
artifacts: the source diff (tests excluded), the full diff, and the lists of changed source files
and changed test files. Later steps read those lists; nothing here calls a model.
"""

import json
import os
import subprocess


def _git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL
    )
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} in {cwd}: {p.stderr.strip()}")
    return p.stdout


def _checkout(tree, sha):
    if not os.path.isdir(os.path.join(tree, ".git")) and not os.path.isfile(os.path.join(tree, ".git")):
        raise RuntimeError(f"{tree} is not a git worktree; run targets/<app>/fetch.py --ticket first")
    if _git(tree, "rev-parse", "HEAD").strip() != sha:
        _git(tree, "checkout", "--quiet", "--detach", sha)


def _name_status(head_tree, base, head):
    rows = []
    for line in _git(head_tree, "diff", "--name-status", base, head).splitlines():
        if not line.strip():
            continue
        status, _, path = line.partition("\t")
        if status.startswith("R"):
            # a rename arrives as "R100\told\tnew": record the new path as added, the old as deleted
            old, _, new = path.partition("\t")
            rows.append({"path": old, "status": "D"})
            rows.append({"path": new, "status": "A"})
        else:
            rows.append({"path": path, "status": status[:1]})
    return rows


def _is_test(path, app):
    return path.startswith(app["api_tests_dir"] + "/") or path.startswith(app["browser_tests_dir"] + "/")


def run(inp):
    repo = inp.repo if hasattr(inp, "repo") else inp["repo"]
    ticket = inp.ticket if hasattr(inp, "ticket") else inp["ticket"]
    run_dir = inp.run_dir if hasattr(inp, "run_dir") else inp["run_dir"]
    app, base, head = repo["app"], repo["base"], repo["head"]
    out_dir = os.path.join(run_dir, "implement")
    os.makedirs(out_dir, exist_ok=True)

    for tree, sha in ((repo["base_tree"], base), (repo["head_tree"], head)):
        _checkout(tree, sha)
        for d in app.get("mutmut", {}).get("pre_create_dirs", []):
            os.makedirs(os.path.join(tree, d), exist_ok=True)

    rows = _name_status(repo["head_tree"], base, head)
    changed_source = [r for r in rows if not _is_test(r["path"], app)]
    changed_tests = [r for r in rows if _is_test(r["path"], app)]
    excludes = [f":!{app['api_tests_dir']}", f":!{app['browser_tests_dir']}"]
    source_diff = _git(repo["head_tree"], "diff", base, head, "--", ".", *excludes)
    full_diff = _git(repo["head_tree"], "diff", base, head)

    paths = {
        "change_diff": os.path.join(out_dir, "change.diff"),
        "change_full_diff": os.path.join(out_dir, "change_full.diff"),
        "changed_source": os.path.join(out_dir, "changed_source.json"),
        "changed_tests": os.path.join(out_dir, "changed_tests.json"),
    }
    with open(paths["change_diff"], "w") as f:
        f.write(source_diff)
    with open(paths["change_full_diff"], "w") as f:
        f.write(full_diff)
    with open(paths["changed_source"], "w") as f:
        json.dump(changed_source, f, indent=1)
    with open(paths["changed_tests"], "w") as f:
        json.dump(changed_tests, f, indent=1)

    return {
        "status": "pass",
        "artifacts": paths,
        "reason": f"{len(changed_source)} source files and {len(changed_tests)} test files changed "
        f"between {base[:7]} and {head[:7]} ({ticket['id']})",
        "gate": None,
        "metrics": {"changed_source": len(changed_source), "changed_tests": len(changed_tests)},
    }
