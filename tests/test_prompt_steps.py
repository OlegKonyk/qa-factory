"""Tests for the frame, plan and review steps. No real calls: the runner is injected."""

import io
import json
import string
import subprocess
from pathlib import Path

import pytest

from factory import driver, headless, rounds
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


def test_review_request_changes_without_a_round_left_stops_with_high_findings(inp, tmp_path):
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
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "review"
    assert "a.py:3 weak assert" in out["reason"] and "b.py" not in out["reason"]
    assert out["gate"]["context"]["findings"] == findings
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


def test_review_still_requesting_changes_after_the_fix_stops_instead_of_failing(inp, fix_round):
    out = review.run(inp, runner=verdicts("request_changes", "request_changes"))
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "review"
    assert out["reason"].startswith("review still requests changes after the fix round: a.py:3")
    assert [a["decision"] for a in out["gate"]["answers"]] == ["sign_off", "another_round", "decline"]
    assert out["gate"]["context"]["findings"] == [HIGH]
    assert "review_round1" in out["artifacts"] and out["artifacts"]["tests_manifest"] == "NEW-MANIFEST"


def test_review_fix_round_that_fails_is_returned(inp, fix_round):
    fix_round.update(status="fail", reason="lint: x")
    runner = verdicts("request_changes")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == "review fix round: lint: x"
    assert out["artifacts"]["tests_manifest"] == "NEW-MANIFEST" and "review_round1" in out["artifacts"]
    assert len(runner.calls) == 1


def test_review_without_a_writer_round_left_stops_without_a_fix(inp, fix_round):
    inp["ticket"]["caps"] = {"writer_rounds": 0}
    out = review.run(inp, runner=verdicts("request_changes"))
    assert out["status"] == "needs_person" and out["reason"].startswith("review requests changes")
    assert "inp" not in fix_round


def test_review_uses_its_fix_round_once_per_ticket(inp, fix_round):
    rounds.Ledger(inp["run_dir"]).add("review", "review_fix", 0.1)
    out = review.run(inp, runner=verdicts("request_changes"))
    assert out["status"] == "needs_person" and "inp" not in fix_round


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


def test_a_fix_round_still_capped_on_resume_fails_review_as_the_fix_round(inp, tmp_path, monkeypatch):
    report = tmp_path / "verify_report.json"
    report.write_text(json.dumps({"status": "fail", "resumable": True, "stopped_at": "test_cases"}))
    inp["artifacts"]["verify_report"] = str(report)
    seen = []

    def run(step_input):
        seen.append(step_input)
        reason = "spend cap reached: 15.00 of 15.00 USD spent on this ticket"
        return {"status": "fail", "artifacts": {"verify_report": str(report)}, "reason": reason, "gate": None}

    monkeypatch.setattr(review.verify, "resume_after_cap", run)
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == (
        "review fix round: spend cap reached: 15.00 of 15.00 USD spent on this ticket"
    )
    assert out["artifacts"]["verify_report"] == str(report) and "review_round1" in out["artifacts"]
    assert len(seen) == 1 and runner.calls == []


def test_a_resumable_report_that_cannot_resume_fails_without_a_writer_round(inp, monkeypatch):
    report = Path(inp["run_dir"]) / "verify" / "report.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"status": "fail", "resumable": True, "rounds": []}))
    inp["artifacts"]["verify_report"] = str(report)
    inp["repo"]["app"]["name"] = "demo"
    monkeypatch.setattr(
        review.verify, "_attempt", lambda *a, **k: pytest.fail("a fresh writer round started")
    )
    runner = verdicts("approve")
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == (
        "review fix round: the capped round's checks are not all on disk and passed; "
        "re-run Verify for this ticket"
    )
    assert runner.calls == []


def test_a_review_call_ended_at_its_budget_is_a_named_cap_hit_with_its_spend_counted(inp):
    def runner(argv, **kwargs):
        raw = {"subtype": "error_max_budget_usd", "is_error": True, "result": "", "total_cost_usd": 1.02}
        return subprocess.CompletedProcess(argv, 1, json.dumps(raw), "")

    out = review.run(inp, runner=runner)
    assert out["status"] == "fail" and out["reason"] == (
        "spend cap reached: the review ended at its budget of 1.00 USD; "
        "1.02 of 15.00 USD spent on this ticket"
    )
    ledger = json.loads((Path(inp["run_dir"]) / "rounds.json").read_text())
    assert [(e["kind"], e["cost_usd"]) for e in ledger["entries"]] == [("review", 1.02)]


def test_a_failed_call_with_empty_text_names_its_subtype(inp):
    def runner(argv, **kwargs):
        raw = {"subtype": "error_during_execution", "is_error": True, "result": ""}
        return subprocess.CompletedProcess(argv, 1, json.dumps(raw), "")

    out = frame.run(inp, runner=runner)
    assert out["reason"] == "frame call failed: error_during_execution" and "budget_exceeded" not in out


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


# The gates of Plan and Review, through the driver's run_step so the record that asked is on disk.


def step_run(fn, inp, index, name):
    run_dir = Path(inp["run_dir"])
    (run_dir / "steps").mkdir(parents=True, exist_ok=True)
    return driver.run_step(
        index, name, fn, inp["ticket"], inp["repo"], run_dir, inp["artifacts"], out=io.StringIO()
    ).to_dict()


def answer(inp, data):
    (Path(inp["run_dir"]) / "answer.json").write_text(json.dumps(data))


PLAN = {"tests": [{"surface": "api", "file": "t.py", "name": "n", "covers": ["AC1"], "reason": "r"}]}


def planned(**fields):
    runner = canned({**PLAN, "placement_reason": "r", "risk": "low", "unknown_patterns": [], **fields})
    return lambda step_input: plan.run(step_input, runner=runner)


@pytest.mark.parametrize(
    "fields, shown",
    [({"risk": "high"}, "risk: high"), ({"unknown_patterns": ["a fake clock"]}, "a fake clock")],
)
def test_plan_stops_on_high_risk_and_on_unknown_patterns(inp, fields, shown):
    out = step_run(planned(**fields), inp, 2, "plan")
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "plan"
    assert shown in out["gate"]["question"]
    assert [a["decision"] for a in out["gate"]["answers"]] == ["approve", "edit", "decline"]


def test_plan_passes_on_low_risk_and_stops_under_person(inp):
    assert step_run(planned(), inp, 2, "plan")["status"] == "pass"
    inp["ticket"]["gates"] = {"plan": "person"}
    inp["run_dir"] = inp["run_dir"] + "-person"
    assert step_run(planned(), inp, 2, "plan")["status"] == "needs_person"


def test_plan_approve_passes_with_the_recorded_plan(inp):
    asked = step_run(planned(risk="high"), inp, 2, "plan")
    answer(inp, {"decision": "approve", "by": "Oleg"})
    out = step_run(planned(), inp, 2, "plan")
    assert out["status"] == "pass" and out["reason"] == "plan approved by Oleg:"
    assert out["artifacts"]["plan"] == asked["artifacts"]["plan"]


@pytest.mark.parametrize("how", ["path", "relative path", "inline"])
def test_plan_edit_replaces_the_plan_and_keeps_the_old_one(inp, tmp_path, how):
    asked = step_run(planned(risk="high"), inp, 2, "plan")
    edited = {"tests": [], "placement_reason": "none needed", "risk": "low", "unknown_patterns": []}
    carried = edited
    if how != "inline":
        (Path(inp["run_dir"]) / "edited-plan.json").write_text(json.dumps(edited))
        carried = (
            "edited-plan.json" if how == "relative path" else str(Path(inp["run_dir"]) / "edited-plan.json")
        )
    answer(inp, {"decision": "edit", "plan": carried, "by": "Oleg"})
    out = step_run(planned(), inp, 2, "plan")
    assert out["status"] == "pass" and out["reason"] == "plan edited by Oleg"
    path = Path(out["artifacts"]["plan"])
    assert path == Path(asked["artifacts"]["plan"])
    assert json.loads(path.read_text())["structured"] == edited
    assert json.loads(path.with_name("plan.before-edit.json").read_text())["structured"]["risk"] == "high"


def test_plan_edit_may_point_at_the_plan_file_edited_in_place(inp):
    asked = step_run(planned(risk="high"), inp, 2, "plan")
    path = Path(asked["artifacts"]["plan"])
    wrapper = json.loads(path.read_text())
    edited = {**wrapper["structured"], "tests": [], "risk": "low"}
    path.write_text(json.dumps({**wrapper, "structured": edited}))
    answer(inp, {"decision": "edit", "plan": "plan/plan.json", "by": "Oleg"})
    out = step_run(planned(), inp, 2, "plan")
    assert out["status"] == "pass" and out["reason"] == "plan edited by Oleg"
    written = json.loads(path.read_text())
    assert written["structured"] == edited and written["edited_by"] == "Oleg"
    assert "structured" not in written["structured"]


def test_plan_edit_with_an_unusable_plan_asks_again_naming_both_forms(inp):
    step_run(planned(risk="high"), inp, 2, "plan")
    (Path(inp["run_dir"]) / "not-a-plan.json").write_text(json.dumps({"steps": []}))
    answer(inp, {"decision": "edit", "plan": "not-a-plan.json", "by": "Oleg"})
    out = step_run(planned(), inp, 2, "plan")
    assert out["status"] == "needs_person" and out["gate"]["kind"] == "plan"
    assert out["reason"].startswith("answer by Oleg not used: ")
    assert 'an object with a "tests" list' in out["reason"]
    assert 'the plan file itself (plan/plan.json, with that object under "structured")' in out["reason"]


def test_plan_decline_fails(inp):
    step_run(planned(risk="high"), inp, 2, "plan")
    answer(inp, {"decision": "decline", "by": "Oleg", "note": "wrong folder"})
    out = step_run(planned(), inp, 2, "plan")
    assert out["status"] == "fail" and out["reason"] == "plan declined by Oleg: wrong folder"


def reviewed(runner):
    return lambda step_input: review.run(step_input, runner=runner)


def test_review_sign_off_passes_with_the_review_and_the_note(inp, fix_round):
    runner = verdicts("request_changes", "request_changes")
    asked = step_run(reviewed(runner), inp, 5, "review")
    assert asked["status"] == "needs_person"
    answer(inp, {"decision": "sign_off", "note": "the finding is cosmetic", "by": "Oleg"})
    out = step_run(reviewed(runner), inp, 5, "review")
    assert out["status"] == "pass" and out["reason"] == "review signed off by Oleg: the finding is cosmetic"
    assert out["artifacts"]["review"] == asked["artifacts"]["review"]
    assert out["artifacts"]["tests_manifest"] == "NEW-MANIFEST" and len(runner.calls) == 2


def test_review_another_round_with_a_round_left_fixes_and_reviews_again(inp, fix_round):
    runner = verdicts("request_changes", "request_changes", "approve")
    step_run(reviewed(runner), inp, 5, "review")
    fix_round.clear()
    answer(inp, {"decision": "another_round", "by": "Oleg"})
    out = step_run(reviewed(runner), inp, 5, "review")
    assert out["status"] == "pass", out["reason"]
    assert fix_round["review"]["findings"] == [HIGH] and "answer" not in fix_round["inp"]["artifacts"]
    assert fix_round["inp"]["artifacts"]["tests_manifest"] == "NEW-MANIFEST"
    assert len(runner.calls) == 3
    folder = Path(inp["run_dir"]) / "review"
    assert (folder / "review.round1.json").is_file() and (folder / "review.round2.json").is_file()
    assert out["artifacts"]["review_round2"] == str(folder / "review.round2.json")


def test_review_another_round_without_a_round_left_fails_with_the_reason(inp, fix_round):
    inp["ticket"]["caps"] = {"writer_rounds": 0}
    runner = verdicts("request_changes")
    step_run(reviewed(runner), inp, 5, "review")
    answer(inp, {"decision": "another_round", "by": "Oleg"})
    out = step_run(reviewed(runner), inp, 5, "review")
    assert out["status"] == "fail"
    assert out["reason"].startswith(
        "another round asked by Oleg, but no writer round is left: review requests"
    )
    assert "inp" not in fix_round and len(runner.calls) == 1


def test_review_decline_fails(inp, fix_round):
    runner = verdicts("request_changes", "request_changes")
    step_run(reviewed(runner), inp, 5, "review")
    answer(inp, {"decision": "decline", "by": "Oleg", "note": "write them again"})
    out = step_run(reviewed(runner), inp, 5, "review")
    assert out["status"] == "fail" and out["reason"] == "review declined by Oleg: write them again"


def test_review_under_person_stops_on_approve_for_sign_off(inp):
    inp["ticket"]["gates"] = {"review": "person"}
    runner = verdicts("approve")
    asked = step_run(reviewed(runner), inp, 5, "review")
    assert asked["status"] == "needs_person" and asked["gate"]["kind"] == "review"
    assert [a["decision"] for a in asked["gate"]["answers"]] == ["sign_off", "decline"]
    answer(inp, {"decision": "another_round", "by": "Oleg"})  # not an answer this question accepts
    assert step_run(reviewed(runner), inp, 5, "review")["status"] == "needs_person"
    answer(inp, {"decision": "sign_off", "by": "Oleg"})
    assert step_run(reviewed(runner), inp, 5, "review")["status"] == "pass"


def test_verify_gate_in_the_fix_round_is_still_answered_through_verify(inp, fix_round, monkeypatch):
    fix_round.update(status="needs_person", reason="ready for approval")
    real_fake = review.verify.repair_from_review

    def gated(step_input, review_data):
        out = real_fake(step_input, review_data)
        return {**out, "gate": {"kind": "approval", "who": "Oleg", "question": "Approve?", "answers": []}}

    monkeypatch.setattr(review.verify, "repair_from_review", gated)
    resumed = []

    def resume(step_input):
        resumed.append(step_input["artifacts"]["answer"])
        return {"status": "pass", "artifacts": {"tests_manifest": "APPROVED"}, "reason": "", "gate": None}

    monkeypatch.setattr(review.verify, "resume", resume)
    runner = verdicts("request_changes", "approve")
    asked = step_run(reviewed(runner), inp, 5, "review")
    assert asked["status"] == "needs_person" and asked["gate"]["kind"] == "approval"
    answer(inp, {"decision": "approve", "by": "Oleg"})
    out = step_run(reviewed(runner), inp, 5, "review")
    assert out["status"] == "pass", out["reason"]
    assert len(resumed) == 1 and out["artifacts"]["tests_manifest"] == "APPROVED"
    assert out["artifacts"]["review_round1"].endswith("review.round1.json") and len(runner.calls) == 2
