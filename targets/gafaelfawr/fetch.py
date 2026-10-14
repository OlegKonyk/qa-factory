"""Set up the gafaelfawr clone the factory runs against.

Usage: uv run python targets/gafaelfawr/fetch.py [--ticket PATH] [--from LOCAL_MIRROR]

Standard library only. Safe to run again: steps that are already done report ok and change nothing.
gafaelfawr is a uv project with a `src/` layout and a second package, `rubin.gafaelfawr`, under
`client/src`, installed editable from the clone by its `dev` group. The environment is the clone's
`.venv` from `uv sync --frozen --inexact` (inexact, so a later sync keeps ruff and mutmut), plus ruff
and mutmut. Both editable installs point at the clone, so a worktree imports its own code only with
`src` and `client/src` first on the path (the recipe's `-o pythonpath=src client/src`); the last step
checks that with PYTHONPATH set the same way. The suite starts Postgres and Redis through
testcontainers, so Docker must be running when tests run; this script does not start containers.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = "https://github.com/lsst-sqre/gafaelfawr"
# Release 16.0.2 (2026-09-22) is newer than the tickets' commits.
PIN = "2a7e4f955d86ff63abe2a0b54ad0d76b3c315890"
PIN_NAME = "16.0.2"
PYTHON = "3.14"  # requires-python >= 3.14
EXTRA = ["ruff", "mutmut==3.8.0"]  # ruff is in the project's lint group, which uv sync skips
IMPORTS = (
    "import gafaelfawr, rubin.gafaelfawr, pytest, testcontainers, mutmut;"
    " assert mutmut.__version__ == '3.8.0'"
)

failures = 0


def report(ok: bool, what: str, detail: str = "") -> bool:
    global failures
    if not ok:
        failures += 1
    print(("ok    " if ok else "FAIL  ") + what + (f"  {detail}" if detail and not ok else ""))
    return ok


def run(args: list, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, env=env)


def step(what: str, args: list, cwd: Path | None = None) -> bool:
    proc = run(args, cwd)
    return report(proc.returncode == 0, what, (proc.stderr or proc.stdout).strip()[-400:])


def head_of(path: Path) -> str:
    proc = run(["git", "-C", path, "rev-parse", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else ""


def ensure_clone(repo: Path, source: str | None) -> bool:
    if (repo / ".git").exists():
        return report(True, f"clone present: {repo}")
    repo.parent.mkdir(parents=True, exist_ok=True)
    if not step(f"clone {source or UPSTREAM}", ["git", "clone", source or UPSTREAM, repo]):
        return False
    if source:
        return step("set origin to upstream", ["git", "-C", repo, "remote", "set-url", "origin", UPSTREAM])
    return True


def ensure_pin(repo: Path) -> bool:
    if head_of(repo) == PIN:
        return report(True, f"checked out {PIN_NAME} {PIN[:7]} (detached)")
    if run(["git", "-C", repo, "cat-file", "-e", f"{PIN}^{{commit}}"]).returncode != 0:
        step("fetch origin", ["git", "-C", repo, "fetch", "origin", "--tags"])
    return step(f"checkout {PIN_NAME} {PIN[:7]} (detached)", ["git", "-C", repo, "checkout", "--detach", PIN])


def ensure_env(repo: Path, py: Path) -> bool:
    have = py.exists() and run([py, "-c", IMPORTS]).returncode == 0
    have = have and run([py, "-m", "ruff", "--version"]).returncode == 0
    if have:
        return report(
            True,
            "gafaelfawr, rubin.gafaelfawr (editable), pytest, testcontainers, ruff, mutmut==3.8.0 installed",
        )
    if not step(
        f"uv sync --frozen --inexact --python {PYTHON}",
        ["uv", "sync", "--frozen", "--inexact", "--python", PYTHON],
        cwd=repo,
    ):
        return False
    return step(f"install {' '.join(EXTRA)}", ["uv", "pip", "install", "--python", py, *EXTRA], cwd=repo)


def ensure_agent_file(repo: Path) -> bool:
    # The upstream repository has no agent file; ours is kept beside the recipe, copied into the
    # clone and excluded from git there so it can never be committed upstream.
    target = repo / "AGENTS.md"
    source = HERE / "AGENTS.md"
    exclude = repo / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if "/AGENTS.md" not in lines:
        exclude.write_text("\n".join([*lines, "/AGENTS.md"]) + "\n")
    if target.exists() and target.read_text() == source.read_text():
        return report(True, "AGENTS.md in the clone (git-excluded)")
    shutil.copyfile(source, target)
    return report(True, "AGENTS.md copied into the clone (git-excluded)")


def ensure_worktree(repo: Path, wt: Path, sha: str, py: Path) -> bool:
    name = f"{wt.parent.name}/{wt.name}"
    if (wt / ".git").exists():
        if head_of(wt) == sha:
            ok = report(True, f"worktree {name} at {sha[:7]}")
        else:
            ok = step(f"worktree {name} moved to {sha[:7]}", ["git", "-C", wt, "checkout", "--detach", sha])
    else:
        wt.parent.mkdir(parents=True, exist_ok=True)
        ok = step(
            f"worktree {name} created at {sha[:7]}",
            ["git", "-C", repo, "worktree", "add", "--detach", wt, sha],
        )
    if ok:
        # The editable installs point at the clone; with src and client/src first on the path (what
        # the recipe's pytest_args do), the worktree's code must win for both packages.
        env = {**os.environ, "PYTHONPATH": "src:client/src"}
        code = (
            "import gafaelfawr, rubin.gafaelfawr;"
            " print(gafaelfawr.__file__); print(rubin.gafaelfawr.__file__)"
        )
        proc = run([py, "-c", code], cwd=wt, env=env)
        where = proc.stdout.split()
        ok = report(
            len(where) == 2 and all(w.startswith(str(wt) + "/") for w in where),
            f"worktree {name} imports its own gafaelfawr and rubin.gafaelfawr",
            " ".join(where) or proc.stderr.strip()[-400:],
        )
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ticket", help="ticket JSON; creates worktrees at its base and head commits")
    ap.add_argument("--from", dest="mirror", help="clone from this local path, then point origin at upstream")
    args = ap.parse_args()

    app = json.loads((HERE / "app.json").read_text())
    repo = Path(app["repo"]).expanduser()
    wts = Path(app["worktrees"]).expanduser()
    py = Path(app["python"]).expanduser()

    if ensure_clone(repo, args.mirror) and ensure_pin(repo):
        ensure_env(repo, py)
        ensure_agent_file(repo)
    if args.ticket:
        # One worktree pair per ticket (the driver's rule), so tickets never share a tree.
        ticket = json.loads(Path(args.ticket).read_text())
        for name in ("base", "head"):
            ensure_worktree(repo, wts / ticket["id"] / name, ticket[name], py)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
