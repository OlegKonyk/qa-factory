"""The Ship step commits the approved tests and cases on a branch and runs the suite."""

import json
import os
import subprocess
import sys

import pytest

from factory.steps import ship


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
def world(tmp_path):
    head = tmp_path / "head"
    head.mkdir()
    git(head, "init", "-q")
    (head / "tests").mkdir()
    (head / "tests" / "test_old.py").write_text("def test_old():\n    assert True\n")
    git(head, "add", ".")
    git(head, "commit", "-q", "-m", "head")
    git(head, "checkout", "-q", "--detach")
    # the generated test, present in the tree but untracked, as Verify leaves it
    (head / "tests" / "test_new.py").write_text("def test_new():\n    assert 1 + 1 == 2\n")
    run = tmp_path / "run"
    (run / "verify" / "testcases" / "demo").mkdir(parents=True)
    (run / "verify" / "testcases" / "demo" / "TC-demo-001.md").write_text("# TC-demo-001: x\n")
    manifest = run / "verify" / "tests_manifest.json"
    manifest.write_text(json.dumps({"files": ["tests/test_new.py"]}))
    app = {
        "name": "demo",
        "python": sys.executable,
        "pytest_args": ["-p", "no:cacheprovider"],
        "api_tests_dir": "tests",
        "browser_tests_dir": "e2e",
        "browser_test_files": "e2e_test_*.py",
        "suite": [["tests"]],
    }
    return {
        "inp": {
            "repo": {"app": app, "head_tree": str(head), "base_tree": ""},
            "ticket": {"id": "demo-x", "title": "demo feature"},
            "artifacts": {"tests_manifest": str(manifest), "test_cases": str(run / "verify" / "testcases")},
            "round": 1,
            "run_dir": str(run),
        },
        "head": head,
    }


def test_ship_commits_tests_and_cases_and_runs_the_suite(world):
    out = ship.run(world["inp"])

    assert out["status"] == "pass", out["reason"]
    head = world["head"]
    assert git(head, "branch", "--show-current").strip() == "qa/demo-x"
    committed = git(head, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(committed) == ["testcases/demo/TC-demo-001.md", "tests/test_new.py"]
    assert "Add QA tests for demo feature" in git(head, "log", "-1", "--format=%s")
    report = json.load(open(out["artifacts"]["ship_report"]))
    assert report["suite"]["status"] == "pass"
    assert "2 passed" in report["suite"]["runs"][0]["summary"]


def test_ship_fails_when_the_suite_is_red(world):
    (world["head"] / "tests" / "test_new.py").write_text("def test_new():\n    assert False\n")
    out = ship.run(world["inp"])
    assert out["status"] == "fail"
    assert "suite red" in out["reason"]
