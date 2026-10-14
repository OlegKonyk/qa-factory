"""Tests for the driver: resume, gate, failure rounds and the command line."""

import hashlib
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


def approval_gate_output(_):
    out = gate_output(_)
    out["gate"].update(
        kind="approval",
        answers=[
            {"decision": "approve", "means": "the tests join the suite"},
            {"decision": "decline", "means": "the step fails"},
        ],
    )
    return out


def test_question_lists_kind_accepted_answers_and_an_example_with_by(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    question = (tmp_path / "runs" / "t-1" / "question.md").read_text()
    assert "Kind: approval" in question and "Who: Oleg" in question
    assert "- `approve`: the tests join the suite" in question
    assert '{"decision": "approve", "by": "Oleg", "note": ""}' in question


def test_an_answer_without_by_is_refused_and_left_in_place(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    run_dir = tmp_path / "runs" / "t-1"
    answer = run_dir / "answer.json"
    answer.write_text(json.dumps({"decision": "approve", "note": "fine"}))
    calls = []
    code, text = go(ticket_path, tmp_path, make_steps(calls))
    assert code == 2
    assert calls == [], "the step must not run on a refused answer"
    assert 'answer: missing field "by"' in text
    assert f"question: {run_dir / 'question.md'}" in text
    assert answer.exists() and not list((run_dir / "steps").glob("*.answer*.json"))


def test_an_unknown_decision_is_refused(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    (tmp_path / "runs" / "t-1" / "answer.json").write_text(json.dumps({"decision": "maybe", "by": "Oleg"}))
    code, text = go(ticket_path, tmp_path, make_steps([]))
    assert code == 2 and "answer: unknown decision 'maybe'" in text


def test_a_gate_calls_the_notifier_once_and_its_failure_does_not_fail_the_run(
    ticket_path, tmp_path, monkeypatch
):
    seen = []

    def notifier(run_dir, step, gate, ticket, app):
        seen.append((run_dir, step, gate.kind, ticket["id"], app["name"]))
        raise RuntimeError("no network")

    monkeypatch.setattr(driver, "NOTIFY", notifier)
    code, text = go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    assert code == 2
    assert seen == [(tmp_path / "runs" / "t-1", "verify", "approval", "t-1", "tiny")]
    assert "notify: RuntimeError: no network" in text
    go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    assert len(seen) == 1, "a re-run that only reprints the question does not tell again"


def test_the_archived_answer_carries_answered_at_and_status_names_the_answerer(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([], {"verify": approval_gate_output}))
    run_dir = tmp_path / "runs" / "t-1"
    original = {"approved": True, "by": "Dana", "note": "fine"}
    (run_dir / "answer.json").write_text(json.dumps(original))
    assert go(ticket_path, tmp_path, make_steps([]))[0] == 0
    archived = json.loads((run_dir / "steps" / "04-verify.answer2.json").read_text())
    assert {k: archived[k] for k in original} == original
    assert archived["answered_at"].startswith("20")
    out = io.StringIO()
    driver.status(run_dir, out)
    verify_line = [line for line in out.getvalue().splitlines() if line.startswith("4 verify")][0]
    assert "answered by Dana (approve)" in verify_line


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
        (run_dir / "answer.json").write_text(json.dumps({"approved": True, "by": "Oleg"}))
        calls.clear()
        steps = make_steps(calls)  # verify now passes with the answer
        assert driver.run(ticket_path, runs_root="runs-rel", steps=steps) == 0
        assert calls[0][1]["artifacts"]["answer"].endswith("answer.json")
        assert not (run_dir / "answer.json").exists(), "the answer must not answer a later gate"
        assert (run_dir / "steps" / "04-verify.answer2.json").exists()
        assert (run_dir / "steps" / "04-verify.round1.json").exists(), "the question it answered is kept"
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


# The clarified ticket


def with_caps(ticket_path, caps):
    ticket = json.loads(ticket_path.read_text())
    ticket.update(caps=caps, description="old", contract=["old"])
    ticket_path.write_text(json.dumps(ticket))


def test_the_clarified_ticket_merges_and_the_ticket_files_caps_win(ticket_path, tmp_path):
    with_caps(ticket_path, {"usd": 2.0})
    run_dir = tmp_path / "runs" / "t-1"
    run_dir.mkdir(parents=True)
    clarified = {"contract": ["GET /x returns 200"], "acceptance_criteria": ["x is listed"]}
    (run_dir / "ticket.clarified.json").write_text(json.dumps(clarified))
    calls = []
    assert go(ticket_path, tmp_path, make_steps(calls))[0] == 0
    for _, step_input in calls:
        ticket = step_input["ticket"]
        assert ticket["contract"] == ["GET /x returns 200"] and ticket["acceptance_criteria"] == [
            "x is listed"
        ]
        assert ticket["description"] == "old" and ticket["caps"] == {"usd": 2.0}
    assert json.loads((run_dir / "ticket.json").read_text())["contract"] == ["GET /x returns 200"]


def test_a_clarified_ticket_with_a_foreign_key_is_rejected(ticket_path, tmp_path):
    run_dir = tmp_path / "runs" / "t-1"
    run_dir.mkdir(parents=True)
    (run_dir / "ticket.clarified.json").write_text(json.dumps({"contract": ["c"], "caps": {"usd": 99}}))
    with pytest.raises(ValueError, match="found caps"):
        driver.prepare(ticket_path, tmp_path / "runs")


# redo


def redo(run_dir, step, *flags):
    out = io.StringIO()
    rerun = "--rerun" in flags
    code = driver.redo(run_dir, step, "Oleg", note="tightened AC2", rerun=rerun, out=out)
    return code, out.getvalue()


def test_redo_archives_later_records_and_writes_its_record(ticket_path, tmp_path):
    plan_file = tmp_path / "plan.json"
    plan_file.write_text('{"structured": {"tests": []}}')

    def plan_step(_):
        return {"status": "pass", "artifacts": {"plan": str(plan_file), "gone": "/no/such"}, "reason": ""}

    go(ticket_path, tmp_path, make_steps([], {"plan": plan_step}))
    run_dir = tmp_path / "runs" / "t-1"
    steps = run_dir / "steps"
    # A record written before records kept hashes: "before" is unknown.
    older = json.loads((steps / "02-plan.json").read_text())
    del older["artifact_sha256"]
    (steps / "02-plan.json").write_text(json.dumps(older))
    code, text = redo(run_dir, "plan")
    assert code == 0
    for name in ("03-implement", "04-verify", "05-review", "06-ship"):
        assert (steps / f"{name}.round1.json").exists() and not (steps / f"{name}.json").exists()
        assert f"archived {name}.round1.json" in text
    assert (steps / "02-plan.json").exists() and "the next run starts at implement" in text
    record = json.loads((steps / "02-plan.redo1.json").read_text())
    assert record["by"] == "Oleg" and record["note"] == "tightened AC2" and record["at"].startswith("20")
    digest = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    assert record["sha256_before"] == {"plan": "unknown", "gone": "unknown"}
    assert record["sha256_after"] == {"plan": digest, "gone": "unknown"}
    calls = []
    out = io.StringIO()
    assert driver.run(ticket_path, runs_root=tmp_path / "runs", steps=make_steps(calls), out=out) == 0
    assert [c[0] for c in calls] == ["implement", "verify", "review", "ship"]
    assert "skip  2 plan" in out.getvalue()
    status = io.StringIO()
    driver.status(run_dir, status)  # the redo record is not a step record
    assert "3 implement pass (earlier round)" in status.getvalue()


def test_redo_takes_before_from_the_passed_record_and_after_from_the_files_now(ticket_path, tmp_path):
    plan_file = tmp_path / "plan.json"
    plan_file.write_text('{"structured": {"tests": []}}')
    folder = tmp_path / "plan-dir"
    folder.mkdir()
    artifacts = {"plan": str(plan_file), "dir": str(folder), "gone": "/no/such"}

    def plan_step(_):
        return {"status": "pass", "artifacts": artifacts, "reason": ""}

    go(ticket_path, tmp_path, make_steps([], {"plan": plan_step}))
    steps = tmp_path / "runs" / "t-1" / "steps"
    passed = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    # Files only: a directory or a missing artifact gets no hash.
    assert json.loads((steps / "02-plan.json").read_text())["artifact_sha256"] == {"plan": passed}
    plan_file.write_text('{"structured": {"tests": [{"name": "edited by hand"}]}}')
    edited = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    assert redo(tmp_path / "runs" / "t-1", "plan")[0] == 0
    record = json.loads((steps / "02-plan.redo1.json").read_text())
    assert record["sha256_before"] == {"plan": passed, "dir": "unknown", "gone": "unknown"}
    assert record["sha256_after"] == {"plan": edited, "dir": "directory", "gone": "unknown"}


def test_a_record_that_is_not_a_pass_keeps_no_hashes(ticket_path, tmp_path):
    def failing(_):
        return {"status": "fail", "artifacts": {"plan": str(ticket_path)}, "reason": "boom"}

    go(ticket_path, tmp_path, make_steps([], {"plan": failing}))
    assert "artifact_sha256" not in json.loads(
        (tmp_path / "runs" / "t-1" / "steps" / "02-plan.json").read_text()
    )


def test_redo_rerun_archives_the_step_itself_and_the_next_round_number_is_free(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([]))
    run_dir = tmp_path / "runs" / "t-1"
    assert redo(run_dir, "verify")[0] == 0
    go(ticket_path, tmp_path, make_steps([]))
    code, text = redo(run_dir, "verify", "--rerun")
    assert code == 0 and "the next run starts at verify" in text
    steps = run_dir / "steps"
    assert (steps / "04-verify.round1.json").exists() and not (steps / "04-verify.json").exists()
    assert (steps / "05-review.round2.json").exists() and (steps / "04-verify.redo2.json").exists()
    calls = []
    go(ticket_path, tmp_path, make_steps(calls))
    assert [c[0] for c in calls] == ["verify", "review", "ship"]


def test_redo_refuses_a_step_not_passed_and_a_run_at_a_gate(ticket_path, tmp_path):
    def failing(_):
        return {"status": "fail", "artifacts": {}, "reason": "boom"}

    go(ticket_path, tmp_path, make_steps([], {"implement": failing}))
    run_dir = tmp_path / "runs" / "t-1"
    code, text = redo(run_dir, "implement")
    assert code == 1 and "has not passed (status fail)" in text
    assert redo(run_dir, "verify")[0] == 1  # no record
    go(ticket_path, tmp_path, make_steps([], {"verify": gate_output}))
    code, text = redo(run_dir, "plan")
    assert code == 1 and "waits at a gate (04-verify.json); answer it first" in text
    assert (run_dir / "steps" / "03-implement.json").exists(), "a refused redo archives nothing"
    assert not list((run_dir / "steps").glob("*.redo*.json"))


def test_command_line_redo(ticket_path, tmp_path):
    go(ticket_path, tmp_path, make_steps([]))
    run_dir = tmp_path / "runs" / "t-1"
    result = subprocess.run(
        [sys.executable, "-m", "factory", "redo", str(run_dir), "review", "--by", "Oleg", "--note", "n"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "archived 06-ship.round1.json" in result.stdout
    assert json.loads((run_dir / "steps" / "05-review.redo1.json").read_text())["by"] == "Oleg"
