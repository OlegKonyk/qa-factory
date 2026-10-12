"""Tests for the driver: resume, gate, failure rounds and the command line."""

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from factory import driver
from factory.driver import STEP_NAMES
from factory.envelope import StepOutput

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def ticket_path(tmp_path):
    app = {"name": "tiny", "worktrees": str(tmp_path / "wt"), "python": "~/venv/bin/python"}
    app_path = tmp_path / "app.json"
    app_path.write_text(json.dumps(app))
    ticket = {"id": "t-1", "app": str(app_path), "base": "aaa", "head": "bbb", "title": "tiny"}
    path = tmp_path / "ticket.json"
    path.write_text(json.dumps(ticket))
    return path


def make_steps(calls, overrides=None):
    """Fake steps that record (name, input) and pass, unless overridden."""
    overrides = overrides or {}

    def build(name):
        def step(step_input):
            calls.append((name, step_input))
            if name in overrides:
                return overrides[name](step_input)
            return {
                "status": "pass",
                "artifacts": {name: f"/x/{name}"},
                "reason": "",
                "gate": None,
                "metrics": {},
            }

        return step

    return {name: build(name) for name in STEP_NAMES}


def go(ticket_path, tmp_path, steps):
    out = io.StringIO()
    code = driver.run(ticket_path, runs_root=tmp_path / "runs", steps=steps, out=out)
    return code, out.getvalue()


def gate_output(_):
    return {
        "status": "needs_person",
        "artifacts": {},
        "reason": "",
        "gate": {"who": "Oleg", "question": "Approve the tests?", "context": {"n": 3}},
        "metrics": {},
    }


def test_all_pass_writes_six_records(ticket_path, tmp_path):
    calls = []
    code, text = go(ticket_path, tmp_path, make_steps(calls))
    run_dir = tmp_path / "runs" / "t-1"
    assert code == 0
    assert [c[0] for c in calls] == STEP_NAMES
    assert len(list((run_dir / "steps").glob("0?-*.json"))) == 6
    assert (run_dir / "ticket.json").exists()
    assert "pass  1 frame" in text


def test_steps_get_repo_trees_and_accumulated_artifacts(ticket_path, tmp_path):
    calls = []
    go(ticket_path, tmp_path, make_steps(calls))
    last = calls[-1][1]
    assert last["repo"]["base_tree"] == str(tmp_path / "wt" / "t-1" / "base")
    assert last["repo"]["head_tree"] == str(tmp_path / "wt" / "t-1" / "head")
    assert last["repo"]["app"]["python"] == str(Path("~/venv/bin/python").expanduser())
    assert set(last["artifacts"]) == set(STEP_NAMES[:-1])
    assert last["round"] == 1


def test_gate_stops_run_and_writes_question(ticket_path, tmp_path):
    calls = []
    code, text = go(ticket_path, tmp_path, make_steps(calls, {"implement": gate_output}))
    run_dir = tmp_path / "runs" / "t-1"
    assert code == 2
    assert [c[0] for c in calls] == ["frame", "plan", "implement"]
    question = (run_dir / "question.md").read_text()
    assert "Approve the tests?" in question
    assert f"{run_dir}/answer.json" in question
    assert "GATE  3 implement: Approve the tests?" in text


def test_rerun_without_answer_reprints_question(ticket_path, tmp_path):
    calls = []
    steps = make_steps(calls, {"implement": gate_output})
    go(ticket_path, tmp_path, steps)
    calls.clear()
    code, text = go(ticket_path, tmp_path, steps)
    assert code == 2
    assert calls == []
    assert "Approve the tests?" in text


def test_rerun_with_answer_resumes_at_gate(ticket_path, tmp_path):
    calls = []
    go(ticket_path, tmp_path, make_steps(calls, {"implement": gate_output}))
    run_dir = tmp_path / "runs" / "t-1"
    (run_dir / "answer.json").write_text(json.dumps({"approved": True, "by": "Oleg", "note": ""}))
    calls.clear()
    code, text = go(ticket_path, tmp_path, make_steps(calls))
    assert code == 0
    assert [c[0] for c in calls] == ["implement", "verify", "review", "ship"]
    assert calls[0][1]["artifacts"]["answer"] == str(run_dir / "answer.json")
    assert "skip  1 frame" in text


def test_failure_stops_then_rerun_is_round_two_and_keeps_round_one(ticket_path, tmp_path):
    calls = []

    def fail(_):
        return {"status": "fail", "artifacts": {}, "reason": "tests are weak", "gate": None, "metrics": {}}

    code, text = go(ticket_path, tmp_path, make_steps(calls, {"verify": fail}))
    steps_dir = tmp_path / "runs" / "t-1" / "steps"
    assert code == 1
    assert "FAIL  4 verify: tests are weak" in text
    assert [c[0] for c in calls][-1] == "verify"

    calls.clear()
    code, _ = go(ticket_path, tmp_path, make_steps(calls))
    assert code == 0
    assert [c[0] for c in calls] == ["verify", "review", "ship"]
    assert calls[0][1]["round"] == 2
    old = json.loads((steps_dir / "04-verify.round1.json").read_text())
    assert old["status"] == "fail"
    assert json.loads((steps_dir / "04-verify.json").read_text())["status"] == "pass"


def test_raising_step_becomes_fail_record(ticket_path, tmp_path):
    def boom(_):
        raise ValueError("bad thing")

    code, text = go(ticket_path, tmp_path, make_steps([], {"plan": boom}))
    record = json.loads((tmp_path / "runs" / "t-1" / "steps" / "02-plan.json").read_text())
    assert code == 1
    assert record["status"] == "fail"
    assert record["output"]["reason"] == "ValueError: bad thing"
    assert "ValueError" in record["output"]["metrics"]["traceback"]
    assert "FAIL  2 plan: ValueError: bad thing" in text


def test_status_lists_every_step(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([], {"review": gate_output}))
    out = io.StringIO()
    driver.status(tmp_path / "runs" / "t-1", out)
    lines = out.getvalue().splitlines()
    assert len(lines) == 5
    assert lines[0].startswith("1 frame pass")
    assert lines[4].startswith("5 review needs_person")


def test_step_output_rejects_unknown_status():
    with pytest.raises(ValueError, match="status"):
        StepOutput(status="maybe")


def test_load_steps_names_the_missing_step(monkeypatch):
    monkeypatch.setattr(driver, "STEP_NAMES", ["frame", "nonexistent_step"])
    with pytest.raises(RuntimeError, match="nonexistent_step"):
        driver.load_steps()


def test_load_steps_finds_every_real_step():
    steps = driver.load_steps()
    assert list(steps) == driver.STEP_NAMES
    assert all(callable(fn) for fn in steps.values())


def test_command_line_usage_error():
    result = subprocess.run(
        [sys.executable, "-m", "factory"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    assert "usage" in result.stderr.lower()


def test_command_line_status(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([]))
    result = subprocess.run(
        [sys.executable, "-m", "factory", "status", str(tmp_path / "runs" / "t-1")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "6 ship pass" in result.stdout


def test_until_stops_after_the_named_step(tmp_path, ticket_path):
    calls = []
    code = driver.run(ticket_path, runs_root=tmp_path / "runs", steps=make_steps(calls), until="plan")
    assert code == 0
    assert [name for name, _ in calls] == ["frame", "plan"]
    with pytest.raises(ValueError, match="unknown step"):
        driver.run(ticket_path, runs_root=tmp_path / "runs", steps=make_steps(calls), until="nope")


def test_run_dir_is_absolute_and_an_answer_is_consumed_once(tmp_path, ticket_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []
    steps = make_steps(calls, {"verify": gate_output})
    assert driver.run(ticket_path, runs_root="runs-rel", steps=steps) == 2
    run_dir = Path(driver.repo_root()) / "runs-rel" / "t-1"
    try:
        assert run_dir.is_dir()
        assert Path(calls[0][1]["run_dir"]).is_absolute()
        (run_dir / "answer.json").write_text(json.dumps({"approved": True}))
        calls.clear()
        steps = make_steps(calls)  # verify now passes with the answer
        assert driver.run(ticket_path, runs_root="runs-rel", steps=steps) == 0
        assert calls[0][1]["artifacts"]["answer"].endswith("answer.json")
        assert not (run_dir / "answer.json").exists(), "the answer must not answer a later gate"
        assert (run_dir / "steps" / "04-verify.answer1.json").exists()
    finally:
        shutil.rmtree(run_dir.parent, ignore_errors=True)


def test_until_stops_at_a_step_that_already_passed(tmp_path, ticket_path):
    driver.run(ticket_path, runs_root=tmp_path / "runs", steps=make_steps([]), until="plan")
    calls = []
    out = io.StringIO()
    code = driver.run(
        ticket_path, runs_root=tmp_path / "runs", steps=make_steps(calls), out=out, until="plan"
    )
    assert code == 0
    assert calls == []
    assert "skip  2 plan" in out.getvalue()
