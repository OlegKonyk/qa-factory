"""Set up the linkding clone the factory runs against.

Usage: uv run python targets/linkding/fetch.py [--ticket PATH] [--from LOCAL_MIRROR] [--prepare-e2e]

Standard library only. Safe to run again: steps that are already done report ok and change nothing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = "https://github.com/sissbruecker/linkding"
TAG = "v1.47.0"
MUTMUT = "mutmut==3.8.0"
DATA_DIRS = ("data/assets", "data/favicons", "data/previews")

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


def ensure_tag(repo: Path) -> bool:
    want = run(["git", "-C", repo, "rev-list", "-n", "1", TAG]).stdout.strip()
    if want and head_of(repo) == want:
        return report(True, f"checked out {TAG} (detached)")
    if not want:
        step("fetch tags", ["git", "-C", repo, "fetch", "--tags", "origin"])
    return step(f"checkout {TAG} (detached)", ["git", "-C", repo, "checkout", "--detach", TAG])


def ensure_env(repo: Path, py: Path) -> bool:
    ok = step("uv sync --python 3.13", ["uv", "sync", "--python", "3.13"], cwd=repo)
    have = py.exists() and run([py, "-c", "import mutmut"]).returncode == 0
    if have:
        return report(True, f"{MUTMUT} installed") and ok
    return step(f"install {MUTMUT}", ["uv", "pip", "install", "--python", py, MUTMUT]) and ok


def ensure_worktree(repo: Path, wt: Path, sha: str) -> bool:
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
        for d in DATA_DIRS:
            (wt / d).mkdir(parents=True, exist_ok=True)
        report(True, f"worktree {name} data directories")
    return ok


def prepare_e2e(wt: Path, py: Path) -> bool:
    ok = step("npm install", ["npm", "install", "--no-audit", "--no-fund"], cwd=wt)
    ok = step("npm run build", ["npm", "run", "build"], cwd=wt) and ok
    ok = step("collectstatic", [py, "manage.py", "collectstatic", "--no-input"], cwd=wt) and ok
    return step("playwright install chromium", [py, "-m", "playwright", "install", "chromium"], cwd=wt) and ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ticket", help="ticket JSON; creates worktrees at its base and head commits")
    ap.add_argument("--from", dest="mirror", help="clone from this local path, then point origin at upstream")
    ap.add_argument(
        "--prepare-e2e",
        action="store_true",
        help="build assets and install the browser in the ticket's head worktree (needs --ticket)",
    )
    args = ap.parse_args()

    app = json.loads((HERE / "app.json").read_text())
    repo = Path(app["repo"]).expanduser()
    wts = Path(app["worktrees"]).expanduser()
    py = Path(app["python"]).expanduser()

    if ensure_clone(repo, args.mirror) and ensure_tag(repo):
        ensure_env(repo, py)
    if args.prepare_e2e and not args.ticket:
        ap.error("--prepare-e2e needs --ticket")
    if args.ticket:
        # One worktree pair per ticket (the driver's rule), so tickets never share a tree.
        ticket = json.loads(Path(args.ticket).read_text())
        for name in ("base", "head"):
            ensure_worktree(repo, wts / ticket["id"] / name, ticket[name])
        if args.prepare_e2e:
            prepare_e2e(wts / ticket["id"] / "head", py)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
