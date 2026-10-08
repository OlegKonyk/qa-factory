"""Tests for the frame, plan and review steps. No real calls: the runner is injected."""

import json
import string
import subprocess
from pathlib import Path

import pytest

from factory import headless
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
    runner = canned({"findings": findings, "verdict": "request_changes"})
    out = review.run(inp, runner=runner)
    assert out["status"] == "fail"
    assert "a.py:3 weak assert" in out["reason"] and "b.py" not in out["reason"]
    assert "bookmarks/tests/test_x_api.py" in runner.seen["argv"][2]
    assert Path(out["artifacts"]["review"]).is_file()


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
    values = dict.fromkeys(["ticket_json", "diff", "strategy", "frame_json", "test_files"], "X")
    assert fields <= set(values)
    assert "X" in text.format_map(values)
    assert "{" not in text.format_map(values)
