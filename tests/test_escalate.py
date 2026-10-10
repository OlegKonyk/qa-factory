import json
import subprocess

import pytest

from factory import escalate


def canned(structured, text="ok", is_error=False):
    raw = {
        "result": text,
        "structured_output": structured,
        "is_error": is_error,
        "total_cost_usd": 0.4,
        "num_turns": 2,
        "duration_ms": 5,
        "usage": {"input_tokens": 3, "output_tokens": 4},
        "modelUsage": {escalate.MODEL: {}},
    }
    seen = {}

    def runner(argv, **kwargs):
        seen["argv"], seen["cwd"] = argv, kwargs["cwd"]
        return subprocess.CompletedProcess(argv, 0, json.dumps(raw), "")

    runner.seen = seen
    return runner


def run_decide(tmp_path, runner, allow_retry=True):
    out = tmp_path / "advice" / "advice.json"
    record = escalate.decide(
        ticket={"title": "Tag search"},
        strategy="STRATEGY",
        diff="+ line {x}",
        failure={"check": "mutation", "reason": "survivors remain", "report": "r.json"},
        history=[{"round": 1, "kind": "repair", "failure": "survivors remain"}],
        test_files=["tests/test_a.py"],
        head_tree=str(tmp_path),
        run_dir=str(tmp_path / "run"),
        allow_retry=allow_retry,
        budget_usd=2.5,
        out_path=str(out),
        runner=runner,
    )
    return record, out


def answer(decision):
    return {"decision": decision, "why": "w", "guidance": "g", "diagnosis": "d"}


@pytest.mark.parametrize("decision", escalate.DECISIONS)
def test_each_decision_is_returned_and_written(tmp_path, decision):
    record, out = run_decide(tmp_path, canned(answer(decision)))
    assert record["decision"] == decision and record["guidance"] == "g"
    assert json.loads(out.read_text()) == record
    assert record["model"] == escalate.MODEL and record["metrics"]["cost_usd"] == 0.4


def test_argv_cwd_and_prompt(tmp_path):
    runner = canned(answer("retry"))
    run_decide(tmp_path, runner)
    argv = runner.seen["argv"]
    assert argv[argv.index("--model") + 1] == "claude-fable-5-1"
    assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"
    assert argv[argv.index("--add-dir") + 1] == str(tmp_path / "run")
    assert argv[argv.index("--max-budget-usd") + 1] == "2.50"
    assert runner.seen["cwd"] == str(tmp_path)
    prompt = argv[2]
    assert "mutation" in prompt and "survivors remain" in prompt and "Tag search" in prompt
    assert "- tests/test_a.py" in prompt and "+ line {x}" in prompt


def test_no_retry_in_schema_when_not_allowed(tmp_path):
    runner = canned(answer("environment"))
    record, _ = run_decide(tmp_path, runner, allow_retry=False)
    argv = runner.seen["argv"]
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    assert "retry" not in schema["properties"]["decision"]["enum"]
    assert "retry" not in record["allowed"]


@pytest.mark.parametrize(
    "runner",
    [
        canned(None, text="boom", is_error=True),
        canned(None, text="plain words"),
        canned(answer("retry")),
    ],
    ids=["error", "no structured output", "outside allowed"],
)
def test_unusable_answers_become_cannot_decide(tmp_path, runner):
    record, out = run_decide(tmp_path, runner, allow_retry=False)
    assert record["decision"] == "cannot_decide"
    assert record["why"].startswith("the stronger model gave no usable answer: ")
    assert out.is_file()
