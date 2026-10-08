"""The Implement step records the developers' commit as the change."""

import json
import os
import subprocess

import pytest

from factory.steps import implement

APP = {
    "name": "demo",
    "api_tests_dir": "tests",
    "browser_tests_dir": "e2e",
    "mutmut": {"pre_create_dirs": ["data/assets"]},
}


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@x",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@x",
        }
    )
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env
    ).stdout


@pytest.fixture
def repo(tmp_path):
    """A repository with a base commit and a head commit that changes source and adds a test."""
    src = tmp_path / "src"
    src.mkdir()
    git(src, "init", "-q")
    (src / "app.py").write_text("def add(a, b):\n    return a - b\n")
    (src / "tests").mkdir()
    (src / "tests" / "test_old.py").write_text("def test_old():\n    assert True\n")
    git(src, "add", ".")
    git(src, "commit", "-q", "-m", "base")
    base = git(src, "rev-parse", "HEAD").strip()
    (src / "app.py").write_text("def add(a, b):\n    return a + b\n")
    (src / "tests" / "test_new.py").write_text(
        "from app import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    )
    (src / "e2e").mkdir()
    (src / "e2e" / "e2e_test_x.py").write_text("def test_x():\n    assert True\n")
    git(src, "add", ".")
    git(src, "commit", "-q", "-m", "head")
    head = git(src, "rev-parse", "HEAD").strip()
    wt = tmp_path / "wt"
    wt.mkdir()
    git(src, "worktree", "add", "-q", "--detach", str(wt / "base"), base)
    git(src, "worktree", "add", "-q", "--detach", str(wt / "head"), base)  # wrong commit on purpose
    return {"base": base, "head": head, "base_tree": str(wt / "base"), "head_tree": str(wt / "head")}


def test_implement_records_the_change_and_fixes_the_worktree(repo, tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    inp = {
        "repo": {"app": APP, **repo},
        "ticket": {"id": "demo-add"},
        "artifacts": {},
        "round": 1,
        "run_dir": str(run_dir),
    }

    out = implement.run(inp)

    assert out["status"] == "pass"
    assert git(repo["head_tree"], "rev-parse", "HEAD").strip() == repo["head"]
    assert os.path.isdir(os.path.join(repo["head_tree"], "data", "assets"))
    changed_source = json.load(open(out["artifacts"]["changed_source"]))
    changed_tests = json.load(open(out["artifacts"]["changed_tests"]))
    assert changed_source == [{"path": "app.py", "status": "M"}]
    assert sorted(r["path"] for r in changed_tests) == ["e2e/e2e_test_x.py", "tests/test_new.py"]
    diff = open(out["artifacts"]["change_diff"]).read()
    assert "return a + b" in diff and "test_new" not in diff
    assert "test_new" in open(out["artifacts"]["change_full_diff"]).read()
    assert out["metrics"] == {"changed_source": 1, "changed_tests": 2}


def test_implement_refuses_a_missing_worktree(repo, tmp_path):
    inp = {
        "repo": {"app": APP, **repo, "head_tree": str(tmp_path / "nowhere")},
        "ticket": {"id": "demo-add"},
        "artifacts": {},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }
    with pytest.raises(RuntimeError, match="not a git worktree"):
        implement.run(inp)
