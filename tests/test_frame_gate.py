"""Frame's gate: the five recorded frames pass under auto; an untestable criterion, a missing
contract or the `person` mode stop it; the answers proceed, clarify and decline. No real calls."""

import io
import json
import subprocess
from pathlib import Path

import pytest

from factory import driver
from factory.driver import STEP_NAMES
from factory.steps import frame

FRAMES = sorted((Path(__file__).parent / "fixtures" / "frames").glob("*.json"))
CLEAN = json.loads(FRAMES[0].read_text())


def runner_of(*answers):
    """A runner that answers each Frame call with the next structured output in turn."""
    calls = []

    def runner(argv, **kwargs):
        structured = answers[min(len(calls), len(answers) - 1)]
        calls.append(argv)
        raw = {"structured_output": structured, "is_error": False, "total_cost_usd": 0.01}
        return subprocess.CompletedProcess(argv, 0, json.dumps(raw), "")

    runner.calls = calls
    return runner


@pytest.fixture
def inp(tmp_path):
    strategy = tmp_path / "strategy.md"
    strategy.write_text("strategy")
    return {
        "ticket": {"id": "t-1", "title": "A ticket", "acceptance_criteria": ["a"]},
        "repo": {"app": {"strategy": str(strategy)}, "base_tree": "x", "head_tree": str(tmp_path)},
        "artifacts": {},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


@pytest.mark.parametrize("path", FRAMES, ids=lambda p: p.stem)
def test_every_recorded_frame_passes_under_auto(inp, path):
    structured = json.loads(path.read_text())
    assert len(structured["ambiguities"]) >= 7  # ambiguities alone never stop a run
    out = frame.run(inp, runner=runner_of(structured))
    assert out["status"] == "pass", out["reason"]
    assert out["gate"] is None


def test_an_untestable_criterion_stops_with_clarify(inp):
    structured = json.loads(FRAMES[1].read_text())
    structured["acceptance_criteria"][2]["testable"] = False
    out = frame.run(inp, runner=runner_of(structured))
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "clarify"
    untestable = out["gate"]["context"]["untestable"]
    assert untestable == [
        f"{structured['acceptance_criteria'][2]['id']}: {structured['acceptance_criteria'][2]['text']}"
    ]
    assert "not testable" in out["gate"]["question"]
    assert out["gate"]["context"]["ambiguities"] == structured["ambiguities"]
    assert [a["decision"] for a in out["gate"]["answers"]] == ["proceed", "clarify", "decline"]
    assert Path(out["artifacts"]["frame"]).is_file()


def test_a_missing_contract_stops_with_clarify(inp):
    structured = {**CLEAN, "missing_contract": ["the route that lists bundles (AC2)"]}
    out = frame.run(inp, runner=runner_of(structured))
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "clarify"
    assert out["gate"]["context"]["missing_contract"] == ["the route that lists bundles (AC2)"]
    assert "the route that lists bundles (AC2)" in out["gate"]["question"]


def test_person_mode_stops_on_a_clean_frame(inp):
    inp["ticket"]["gates"] = {"frame": "person"}
    out = frame.run(inp, runner=runner_of({**CLEAN, "missing_contract": []}))
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "clarify"
    assert out["gate"]["context"]["missing_contract"] == [] and out["gate"]["context"]["untestable"] == []


def test_the_prompt_asks_for_missing_contract():
    text = (Path(frame.__file__).parent.parent / "prompts" / "frame.md").read_text()
    assert "missing_contract" in text and "Leave it empty when the ticket's contract" in text


# Through the driver: the answers.


@pytest.fixture
def world(tmp_path):
    strategy = tmp_path / "strategy.md"
    strategy.write_text("strategy")
    app = {"name": "tiny", "worktrees": str(tmp_path / "wt"), "strategy": str(strategy)}
    (tmp_path / "app.json").write_text(json.dumps(app))
    ticket = {
        "id": "tiny-t",
        "app": str(tmp_path / "app.json"),
        "base": "a",
        "head": "b",
        "title": "tiny",
        "description": "vague",
        "acceptance_criteria": ["it works"],
        "caps": {"usd": 3.0},
    }
    path = tmp_path / "ticket.json"
    path.write_text(json.dumps(ticket))
    return {"ticket": path, "runs": tmp_path / "runs", "run_dir": tmp_path / "runs" / "tiny-t"}


def steps_with(frame_runner, calls):
    def fake(name):
        def step(step_input):
            calls.append((name, step_input))
            return {"status": "pass", "artifacts": {name: f"/x/{name}"}, "reason": "", "gate": None}

        return step

    steps = {name: fake(name) for name in STEP_NAMES}
    steps["frame"] = lambda step_input: frame.run(step_input, runner=frame_runner)
    return steps


def go(world, steps):
    out = io.StringIO()
    return driver.run(world["ticket"], runs_root=world["runs"], steps=steps, out=out), out.getvalue()


def answer(world, data):
    (world["run_dir"] / "answer.json").write_text(json.dumps(data))


MISSING = {**CLEAN, "missing_contract": ["the route path"]}


def test_proceed_passes_with_the_recorded_frame_and_no_new_call(world):
    runner, calls = runner_of(MISSING), []
    code, text = go(world, steps_with(runner, calls))
    assert code == 2 and "GATE  1 frame" in text and calls == []
    assert "clarify" in (world["run_dir"] / "question.md").read_text()
    answer(world, {"decision": "proceed", "by": "Oleg", "note": "the route is obvious"})
    code, _ = go(world, steps_with(runner, calls))
    assert code == 0 and len(runner.calls) == 1
    record = json.loads((world["run_dir"] / "steps" / "01-frame.json").read_text())
    assert record["output"]["reason"] == "proceeded as read by Oleg: the route is obvious"
    frame_path = record["output"]["artifacts"]["frame"]
    assert calls[0][0] == "plan" and calls[0][1]["artifacts"]["frame"] == frame_path
    assert json.loads(Path(frame_path).read_text())["structured"] == MISSING


def test_clarify_frames_the_clarified_ticket_and_every_later_step_gets_it(world):
    runner, calls = runner_of(MISSING, {**CLEAN, "missing_contract": []}), []
    go(world, steps_with(runner, calls))
    contract = ["GET /api/things/ returns 200 with a list"]
    answer(world, {"decision": "clarify", "ticket": {"contract": contract}, "by": "Oleg"})
    code, text = go(world, steps_with(runner, calls))
    assert code == 0, text
    assert len(runner.calls) == 2 and "GET /api/things/" in runner.calls[1][2]  # Frame ran again
    clarified = json.loads((world["run_dir"] / "ticket.clarified.json").read_text())
    assert clarified == {"contract": contract}
    assert [c[0] for c in calls] == STEP_NAMES[1:]
    assert all(c[1]["ticket"]["contract"] == contract for c in calls)
    assert calls[0][1]["ticket"]["caps"] == {"usd": 3.0}
    assert json.loads((world["run_dir"] / "ticket.json").read_text())["contract"] == contract


def test_clarify_applies_the_gate_rule_again(world):
    runner, calls = runner_of(MISSING, MISSING), []
    go(world, steps_with(runner, calls))
    answer(world, {"decision": "clarify", "ticket": {"description": "clearer"}, "by": "Oleg"})
    code, _ = go(world, steps_with(runner, calls))
    assert code == 2 and len(runner.calls) == 2 and calls == []
    record = json.loads((world["run_dir"] / "steps" / "01-frame.json").read_text())
    assert record["status"] == "needs_person" and record["output"]["gate"]["kind"] == "clarify"


def test_a_clarification_with_a_foreign_field_is_not_used_and_the_question_stands(world):
    runner, calls = runner_of(MISSING), []
    go(world, steps_with(runner, calls))
    answer(world, {"decision": "clarify", "ticket": {"caps": {"usd": 99}}, "by": "Oleg"})
    code, _ = go(world, steps_with(runner, calls))
    assert code == 2 and len(runner.calls) == 1
    assert not (world["run_dir"] / "ticket.clarified.json").exists()
    record = json.loads((world["run_dir"] / "steps" / "01-frame.json").read_text())
    assert "found caps" in record["output"]["reason"] and record["output"]["gate"]["kind"] == "clarify"


def test_decline_fails_the_step(world):
    runner, calls = runner_of(MISSING), []
    go(world, steps_with(runner, calls))
    answer(world, {"decision": "decline", "by": "Oleg", "note": "rewrite the ticket"})
    code, text = go(world, steps_with(runner, calls))
    assert code == 1 and "FAIL  1 frame: declined by Oleg: rewrite the ticket" in text
    assert calls == [] and len(runner.calls) == 1
