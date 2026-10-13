"""Set up the isso clone the factory runs against.

Usage: uv run python targets/isso/fetch.py [--ticket PATH] [--from LOCAL_MIRROR]

Standard library only. Safe to run again: steps that are already done report ok and change nothing.
isso is a setuptools project, not a uv project: the environment is a uv virtual environment inside
the clone with isso installed editable (its import reads its own installed version), its test extra,
ruff and mutmut. The factory runs `python -m pytest` from a worktree, so the worktree's code is the
code imported; the last step checks that.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = "https://github.com/isso-comments/isso"
# No release tag is newer than the tickets' commits (0.14.0 is from March 2026), so pin a commit.
PIN = "413d447a46437d0e9ccf206c8525119355e291d4"
PYTHON = "3.13"  # upstream CI tests 3.10 to 3.14
PACKAGES = ["-e", ".[test]", "ruff", "mutmut==3.8.0"]

failures = 0


def report(ok: bool, what: str, detail: str = "") -> bool:
    global failures
    if not ok:
        failures += 1
    print(("ok    " if ok else "FAIL  ") + what + (f"  {detail}" if detail and not ok else ""))
    return ok


def run(args: list, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True)


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
        return report(True, f"checked out {PIN[:7]} (detached)")
    if run(["git", "-C", repo, "cat-file", "-e", f"{PIN}^{{commit}}"]).returncode != 0:
        step("fetch origin", ["git", "-C", repo, "fetch", "origin"])
    return step(f"checkout {PIN[:7]} (detached)", ["git", "-C", repo, "checkout", "--detach", PIN])


def ensure_env(repo: Path, py: Path) -> bool:
    if py.exists():
        report(True, f"virtual environment present ({py})")
    elif not step(
        f"uv venv --python {PYTHON}", ["uv", "venv", "--python", PYTHON, py.parent.parent], cwd=repo
    ):
        return False
    have = (
        run([py, "-c", "import isso, pytest, mutmut; assert mutmut.__version__ == '3.8.0'"]).returncode == 0
    )
    have = have and run([py, "-m", "ruff", "--version"]).returncode == 0
    if have:
        return report(True, "isso (editable), pytest, ruff, mutmut==3.8.0 installed")
    return step(
        "install isso (editable) with test extra, ruff, mutmut==3.8.0",
        ["uv", "pip", "install", "--python", py, *PACKAGES],
        cwd=repo,
    )


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
        # The editable install points at the clone; from the worktree, the worktree's code must win.
        proc = run([py, "-c", "import isso; print(isso.__file__)"], cwd=wt)
        where = proc.stdout.strip()
        ok = report(
            where.startswith(str(wt) + "/"), f"worktree {name} imports its own isso", where or proc.stderr
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
    if args.ticket:
        # One worktree pair per ticket (the driver's rule), so tickets never share a tree.
        ticket = json.loads(Path(args.ticket).read_text())
        for name in ("base", "head"):
            ensure_worktree(repo, wts / ticket["id"] / name, ticket[name], py)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
