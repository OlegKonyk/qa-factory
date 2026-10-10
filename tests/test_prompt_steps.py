"""Tests for the frame, plan and review steps. No real calls: the runner is injected."""

import json
import string
import subprocess
from pathlib import Path

import pytest

from factory import headless, rounds
from factory.steps import frame, plan, review

PROMPT_DIR = Path(headless.__file__).parent / "prompts"


def canned(structured, text="ok"):
    raw = {
        "result": text,
        "structured_output": structured,
        "is_error": False,
        "total_cost_usd": 0.01,
        "num_turns": 2,
        "duration_ms": 5,
        "usage": {"input_tokens": 3, "output_tokens": 4},
        "modelUsage": {"claude-test": {}},
    }
    seen = {}

    def runner(argv, **kwargs):
        seen["argv"], seen["cwd"] = argv, kwargs["cwd"]
        return subprocess.CompletedProcess(argv, 0, json.dumps(raw), "")

    runner.seen = seen
    return runner


@pytest.fixture
def inp(tmp_path):
    strategy = tmp_path / "strategy.md"
    strategy.write_text("PLACE API TESTS HERE")
    diff = tmp_path / "change.diff"
    diff.write_text("+ added line")
    head = tmp_path / "head"
    head.mkdir()
    # An absolute strategy path is used as is.
    return {
        "ticket": {"id": "t-1", "title": "A ticket", "acceptance_criteria": ["a"]},
        "repo": {
            "app": {"strategy": str(strategy)},
            "base": "b",
            "head": "h",
            "base_tree": "x",
            "head_tree": str(head),
        },
        "artifacts": {"change_diff": str(diff)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


def test_frame_writes_artifact_and_metrics(inp):
    structured = {"acceptance_criteria": [], "ambiguities": [], "summary": "s"}
    runner = canned(structured)
    out = frame.run(inp, runner=runner)
    assert out["status"] == "pass" and out["gate"] is None
    path = Path(out["artifacts"]["frame"])
    assert path == Path(inp["run_dir"]) / "frame" / "frame.json"
    saved = json.loads(path.read_text())
    assert saved["structured"] == structured
    assert out["metrics"]["cost_usd"] == 0.01 and out["metrics"]["model"] == "claude-test"
    assert runner.seen["cwd"] == inp["repo"]["head_tree"]
    prompt = runner.seen["argv"][2]
    assert "A ticket" in prompt and "+ added line" in prompt


def test_plan_prompt_has_strategy_and_frame(inp, tmp_path):
    frame_file = tmp_path / "frame.json"
    frame_file.write_text('{"structured": "FRAME-MARKER"}')
    inp["artifacts"]["frame"] = str(frame_file)
    runner = canned({"tests": [], "placement_reason": "r"})
    out = plan.run(inp, runner=runner)
    assert out["status"] == "pass"
    prompt = runner.seen["argv"][2]
    assert "PLACE API TESTS HERE" in prompt and "FRAME-MARKER" in prompt
    assert Path(out["artifacts"]["plan"]).is_file()


def test_review_approve_passes(inp):
    out = review.run(inp, runner=canned({"findings": [], "verdict": "approve"}))
    assert out["status"] == "pass"


def test_review_request_changes_fails_with_high_findings(inp, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": ["bookmarks/tests/test_x_api.py"]}))
    inp["artifacts"]["tests_manifest"] = str(manifest)
    findings = [
        {"file": "a.py", "line": 3, "severity": "high", "summary": "weak assert", "failure_scenario": "f"},
        {"file": "b.py", "line": 9, "severity": "low", "summary": "style", "failure_scenario": "g"},
    ]
    inp["ticket"]["caps"] = {"writer_rounds": 0}  # no writer round left: no fix round
    runner = canned({"findings": findings, "verdict": "request_changes"})
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail"
    assert "a.py:3 weak assert" in out["reason"] and "b.py" not in out["reason"]
    assert "bookmarks/tests/test_x_api.py" in runner.seen["argv"][2]
    assert Path(out["artifacts"]["review"]).is_file()


HIGH = {"file": "a.py", "line": 3, "severity": "high", "summary": "weak assert", "failure_scenario": "f"}


def verdicts(*answers):
    """A runner that answers each review call with the next verdict in turn."""
    calls = []

    def runner(argv, **kwargs):
        verdict = answers[len(calls)]
        calls.append({"argv": argv, "cwd": kwargs["cwd"]})
        findings = [HIGH] if verdict == "request_changes" else []
        raw = {
            "structured_output": {"findings": findings, "verdict": verdict},
            "is_error": False,
            "total_cost_usd": 0.25,
            "modelUsage": {"claude-test": {}},
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(raw), "")

    runner.calls = calls
    return runner


@pytest.fixture
def fix_round(monkeypatch, tmp_path):
    """verify.repair_from_review replaced by a fake that records its arguments and passes."""
    seen = {}

    def fake(inp, review_data):
        seen["inp"], seen["review"] = inp, review_data
        return {
            "status": seen.get("status", "pass"),
            "artifacts": {"tests_manifest": "NEW-MANIFEST", "tests_dir": "NEW-DIR"},
            "reason": seen.get("reason", "every check passed"),
            "gate": None,
            "metrics": {},
        }

    monkeypatch.setattr(review.verify, "repair_from_review", fake)
    return seen


def test_review_fix_round_then_approve_passes_with_the_new_tests(inp, fix_round):
    runner = verdicts("request_changes", "approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "pass", out["reason"]
    assert fix_round["review"]["findings"] == [HIGH]
    assert out["artifacts"]["tests_manifest"] == "NEW-MANIFEST"
    round1 = Path(out["artifacts"]["review_round1"])
    assert round1.name == "review.round1.json" and round1.is_file()
    assert Path(out["artifacts"]["review"]).is_file()
    assert len(runner.calls) == 2


def test_review_still_requesting_changes_after_the_fix_fails(inp, fix_round):
    out = review.run(inp, runner=verdicts("request_changes", "request_changes"))
    assert out["status"] == "fail"
    assert out["reason"].startswith("review still requests changes after the fix round: a.py:3")
    assert "review_round1" in out["artifacts"]


def test_review_fix_round_that_fails_is_returned(inp, fix_round):
    fix_round.update(status="fail", reason="lint: x")
    runner = verdicts("request_changes")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == "review fix round: lint: x"
    assert out["artifacts"]["tests_manifest"] == "NEW-MANIFEST" and "review_round1" in out["artifacts"]
    assert len(runner.calls) == 1


def test_review_without_a_writer_round_left_fails_without_a_fix(inp, fix_round):
    inp["ticket"]["caps"] = {"writer_rounds": 0}
    out = review.run(inp, runner=verdicts("request_changes"))
    assert out["status"] == "fail" and out["reason"].startswith("review requests changes")
    assert "inp" not in fix_round


def test_review_uses_its_fix_round_once_per_ticket(inp, fix_round):
    rounds.Ledger(inp["run_dir"]).add("review", "review_fix", 0.1)
    out = review.run(inp, runner=verdicts("request_changes"))
    assert out["status"] == "fail" and "inp" not in fix_round


def test_review_never_runs_blind_and_its_cost_is_in_the_ledger(inp):
    inp["ticket"]["qa_mode"] = "blind"
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "pass"
    assert runner.calls[0]["cwd"] == inp["repo"]["head_tree"]  # blind would run in the base tree
    assert "+ added line" in runner.calls[0]["argv"][2]  # and would hide the diff
    assert "--settings" not in runner.calls[0]["argv"]
    ledger = json.loads((Path(inp["run_dir"]) / "rounds.json").read_text())
    assert [(e["step"], e["kind"], e["cost_usd"]) for e in ledger["entries"]] == [("review", "review", 0.25)]


def test_review_stops_at_the_spend_cap(inp):
    inp["ticket"]["caps"] = {"usd": 0.1}
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and "spend cap reached" in out["reason"]
    assert runner.calls == []


def test_failed_call_returns_fail(inp):
    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 1, json.dumps({"is_error": True, "result": "boom"}), "")

    out = frame.run(inp, runner=runner)
    assert out["status"] == "fail" and "boom" in out["reason"] and out["artifacts"] == {}


@pytest.mark.parametrize("name", ["frame", "plan", "review"])
def test_prompt_placeholders_resolve(name):
    text = (PROMPT_DIR / name).with_suffix(".md").read_text()
    assert len(text.splitlines()) < 60
    fields = {f for _, f, _, _ in string.Formatter().parse(text) if f}
    values = dict.fromkeys(["ticket_json", "diff", "strategy", "frame_json", "test_files", "where"], "X")
    assert fields <= set(values)
    assert "X" in text.format_map(values)
    assert "{" not in text.format_map(values)


@pytest.mark.parametrize("status", ["fail", "needs_person"])
def test_review_refuses_tests_whose_checks_have_not_passed(inp, tmp_path, status):
    report = tmp_path / "verify_report.json"
    report.write_text(json.dumps({"status": status}))
    inp["artifacts"]["verify_report"] = str(report)
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and f"status {status}" in out["reason"]
    assert runner.calls == []


def test_review_reads_an_answer_to_its_fix_round_through_verify(inp, monkeypatch):
    seen = []

    def resume(step_input):
        seen.append(step_input["artifacts"]["answer"])
        return {"status": "pass", "artifacts": {"tests_manifest": "NEW"}, "reason": "", "gate": None}

    monkeypatch.setattr(review.verify, "resume", resume)
    inp["artifacts"]["answer"] = "/run/answer.json"
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "pass" and seen == ["/run/answer.json"]
    assert out["artifacts"]["tests_manifest"] == "NEW" and len(runner.calls) == 1


def test_a_declined_answer_to_the_fix_round_fails_review_without_a_review(inp, monkeypatch):
    def resume(step_input):
        return {"status": "fail", "artifacts": {}, "reason": "declined by Oleg: no", "gate": None}

    monkeypatch.setattr(review.verify, "resume", resume)
    inp["artifacts"]["answer"] = "/run/answer.json"
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == "review fix round: declined by Oleg: no"
    assert runner.calls == []
