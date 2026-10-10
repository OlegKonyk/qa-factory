"""The Verify loop: repair round, stronger model, caps, answers, blind writer, review fix round.

No model call and no application: checks are faked through ATTEMPT_CHECKS and FINAL_CHECKS,
escalate.decide is replaced by a canned record, and verify.RUNNER by a fake claude.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from factory import rounds
from factory.steps import verify

PASS = {
    "lint": {"status": "pass", "findings": []},
    "revert": {"status": "pass", "tests": {"tests/test_x.py::test_x": {"verdict": "proves-behaviour"}}},
    "mutation": {"skipped": "no function changed"},
    "suite": {"status": "pass", "runs": [{"summary": "1 passed", "returncode": 0}]},
}
FAILED_REPORT = {
    "lint": {
        "status": "fail",
        "findings": [{"file": "tests/test_x.py", "line": 3, "rule": "QA001", "message": "no assertion"}],
    },
    "revert": {
        "status": "fail",
        "tests": {
            "tests/test_x.py::test_x": {
                "at_head": "pass",
                "reverted": "missing-name",
                "verdict": "missing-name",
                "message": "NameError: SORT_MODIFIED",
            }
        },
    },
    "suite": {"status": "fail", "runs": [{"summary": "1 failed", "returncode": 1, "tail": ["E boom"]}]},
}


class Fakes:
    """Scripted checks. `outcomes[name]` lists per call: "pass", "repairable" or "fail" (last repeats)."""

    def __init__(self, monkeypatch, tmp_path, **outcomes):
        self.outcomes, self.calls, self.writes, self.cases = outcomes, {}, [], 0
        self.tmp_path = tmp_path
        checks = [("write_tests", self.write_tests)]
        checks += [(name, self._check(name)) for name in ("lint", "revert", "mutation", "suite")]
        monkeypatch.setattr(verify, "ATTEMPT_CHECKS", checks)
        monkeypatch.setattr(verify, "FINAL_CHECKS", [("test_cases", self.test_cases)])

    def write_tests(self, ctx):
        self.writes.append(
            {
                "round": ctx["round"],
                "kind": ctx["kind"],
                "mode": ctx["mode"],
                "findings": ctx["findings"],
                "guidance": ctx["guidance"],
                "files": list(ctx["files"]),
            }
        )
        ctx["costs"][verify._cost_key(ctx)] = {"cost_usd": 0.5, "model": "writer"}
        ctx["files"] = ["tests/test_x.py"]
        manifest = os.path.join(ctx["out"], "tests_manifest.json")
        Path(manifest).write_text(json.dumps({"files": ctx["files"]}))
        ctx["artifacts_out"]["tests_manifest"] = manifest
        return {"files": ctx["files"]}

    def _check(self, name):
        def check(ctx):
            seen = self.calls.setdefault(name, [])
            seen.append(ctx["round"])
            script = self.outcomes.get(name, ["pass"])
            outcome = script[min(len(seen) - 1, len(script) - 1)]
            if outcome == "pass":
                return PASS[name]
            raise verify.CheckFailed(
                f"{name} broke", repairable=outcome == "repairable", report=FAILED_REPORT.get(name)
            )

        return check

    def test_cases(self, ctx):
        self.cases += 1
        return {"files": ["demo/TC-demo-001.md"]}


class Advisor:
    """escalate.decide replaced: canned decisions in turn, keyword arguments kept."""

    def __init__(self, monkeypatch, *decisions):
        self.decisions, self.calls = decisions, []
        monkeypatch.setattr(verify.escalate, "decide", self)

    def __call__(self, **kwargs):
        decision = self.decisions[min(len(self.calls), len(self.decisions) - 1)]
        self.calls.append(kwargs)
        record = {
            "decision": decision,
            "why": "WHY",
            "guidance": "GUIDANCE: assert the order",
            "diagnosis": "DIAGNOSIS: the change sorts the wrong way",
            "metrics": {"cost_usd": 1.0, "model": "fable", "duration_ms": 2000},
        }
        Path(kwargs["out_path"]).write_text(json.dumps(record))
        return record


def _inp(tmp_path, ticket_extra=None, artifacts=None):
    ticket = {"id": "demo-x", "title": "x", **(ticket_extra or {})}
    return {
        "repo": {"app": {"name": "demo"}, "head_tree": str(tmp_path), "base_tree": str(tmp_path)},
        "ticket": ticket,
        "artifacts": artifacts or {},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


def _report(tmp_path):
    return json.loads((tmp_path / "run" / "verify" / "report.json").read_text())


def _ledger_kinds(tmp_path):
    saved = json.loads((tmp_path / "run" / "rounds.json").read_text())
    return [e["kind"] for e in saved["entries"]]


def test_a_lint_failure_gets_one_repair_round_and_then_passes(tmp_path, monkeypatch):
    fakes = Fakes(monkeypatch, tmp_path, lint=["repairable", "pass"])
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "pass", out["reason"]
    assert [w["mode"] for w in fakes.writes] == ["fresh", "repair"]
    assert "tests/test_x.py:3 QA001 no assertion" in fakes.writes[1]["findings"]
    verify_dir = tmp_path / "run" / "verify"
    assert (verify_dir / "rounds" / "1" / "lint.json").is_file()
    assert (verify_dir / "rounds" / "2" / "lint.json").is_file()
    report = _report(tmp_path)
    assert [(r["round"], r["kind"]) for r in report["rounds"]] == [(1, "write"), (2, "repair")]
    assert report["rounds"][0]["failure"]["check"] == "lint"
    assert _ledger_kinds(tmp_path) == ["write", "repair"]
    assert set(out["metrics"]["costs"]) == {"write_tests", "repair.r2"}
    assert out["metrics"]["cost_usd"] == 1.0 and out["metrics"]["rounds"] == 2
    assert out["metrics"]["ticket_spent_usd"] == 1.0


def test_the_stronger_model_asks_for_a_guided_round_that_passes(tmp_path, monkeypatch):
    fakes = Fakes(monkeypatch, tmp_path, suite=["fail", "pass"])
    advisor = Advisor(monkeypatch, "retry")
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "pass", out["reason"]
    assert [w["kind"] for w in fakes.writes] == ["write", "guided"]
    assert fakes.writes[1]["guidance"] == "GUIDANCE: assert the order"
    assert "E boom" in fakes.writes[1]["findings"]
    assert advisor.calls[0]["allow_retry"] is True
    assert advisor.calls[0]["failure"]["check"] == "suite"
    assert advisor.calls[0]["runner"] is verify.RUNNER
    assert _ledger_kinds(tmp_path) == ["write", "advice", "guided"]
    assert out["artifacts"]["escalation"].endswith("escalation-1.json")


@pytest.mark.parametrize(
    ("decision", "said"),
    [
        ("change_is_wrong", "the stronger model judged the tests right and the change wrong: DIAGNOSIS"),
        ("environment", "environment problem, diagnosed by the stronger model: DIAGNOSIS"),
    ],
)
def test_a_suite_failure_goes_to_the_stronger_model_without_a_repair(tmp_path, monkeypatch, decision, said):
    fakes = Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, decision)
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "fail"
    assert out["reason"].startswith(said)
    assert len(fakes.writes) == 1 and len(advisor.calls) == 1
    assert Path(out["artifacts"]["escalation"]).is_file()
    assert _report(tmp_path)["advice"] == [out["artifacts"]["escalation"]]


def test_cannot_decide_stops_for_a_person(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    Advisor(monkeypatch, "cannot_decide")
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "needs_person"
    assert out["gate"]["context"]["failure"]["check"] == "suite"
    assert "suite broke" in out["gate"]["question"]
    report = _report(tmp_path)
    assert report["gate_kind"] == "escalation" and report["last_failure"]["check"] == "suite"


def test_a_failure_after_the_guided_round_goes_back_without_retry(tmp_path, monkeypatch):
    fakes = Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, "retry", "environment")
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "fail" and out["reason"].startswith("environment problem")
    assert [c["allow_retry"] for c in advisor.calls] == [True, False]
    assert len(fakes.writes) == 2


def test_a_second_repairable_failure_goes_to_the_stronger_model(tmp_path, monkeypatch):
    fakes = Fakes(monkeypatch, tmp_path, lint=["repairable"])
    advisor = Advisor(monkeypatch, "environment")
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "fail"
    assert [w["kind"] for w in fakes.writes] == ["write", "repair"]
    assert advisor.calls[0]["allow_retry"] is True and advisor.calls[0]["failure"]["check"] == "lint"


def test_with_one_writer_round_the_stronger_model_cannot_ask_for_a_retry(tmp_path, monkeypatch):
    fakes = Fakes(monkeypatch, tmp_path, lint=["repairable"])
    advisor = Advisor(monkeypatch, "environment")
    verify.run(_inp(tmp_path, {"caps": {"writer_rounds": 1}}))
    assert [w["kind"] for w in fakes.writes] == ["write", "repair"]
    assert advisor.calls[0]["allow_retry"] is False


def test_without_a_stronger_model_call_left_the_step_fails_naming_the_cap(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, "retry")
    out = verify.run(_inp(tmp_path, {"caps": {"advice": 0}}))
    assert out["status"] == "fail"
    assert out["reason"].startswith("suite: suite broke")
    assert "cap of 0 stronger-model calls" in out["reason"]
    assert advisor.calls == []


def test_the_spend_cap_fails_the_step(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, "retry")
    out = verify.run(_inp(tmp_path, {"caps": {"usd": rounds.MIN_CALL_USD + 0.1}}))
    assert out["status"] == "fail" and out["reason"].startswith("spend cap reached")
    assert advisor.calls == []
    assert _report(tmp_path)["ledger"]["spent_usd"] == 0.5


def test_a_second_verify_run_numbers_its_rounds_after_the_first(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    inp = _inp(tmp_path, {"caps": {"advice": 0}})
    assert verify.run(inp)["status"] == "fail"
    fakes = Fakes(monkeypatch, tmp_path)
    out = verify.run(inp)
    assert out["status"] == "pass", out["reason"]
    assert fakes.writes[0]["round"] == 2
    assert [r["round"] for r in _report(tmp_path)["rounds"]] == [2]
    assert (tmp_path / "run" / "verify" / "rounds" / "1" / "suite.json").is_file()


def _escalated(tmp_path, monkeypatch):
    """A Verify run parked at the escalation gate, and the answer file for it."""
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    Advisor(monkeypatch, "cannot_decide")
    inp = _inp(tmp_path)
    assert verify.run(inp)["status"] == "needs_person"
    answer = tmp_path / "run" / "answer.json"
    return {**inp, "artifacts": {"answer": str(answer)}}, answer


def test_a_person_answers_retry_and_a_guided_round_passes(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    answer.write_text(json.dumps({"decision": "retry", "guidance": "use two bookmarks", "by": "Oleg"}))
    fakes = Fakes(monkeypatch, tmp_path)
    advisor = Advisor(monkeypatch, "environment")
    out = verify.run(inp)
    assert out["status"] == "pass", out["reason"]
    assert [(w["kind"], w["round"]) for w in fakes.writes] == [("guided", 2)]
    assert fakes.writes[0]["guidance"] == "use two bookmarks"
    assert "suite broke" in fakes.writes[0]["findings"]
    assert advisor.calls == []
    assert _ledger_kinds(tmp_path) == ["write", "advice", "guided"]
    assert [r["round"] for r in _report(tmp_path)["rounds"]] == [1, 2]


def test_a_person_answers_another_decision_and_the_step_fails(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    answer.write_text(json.dumps({"decision": "stop", "note": "not worth it", "by": "Oleg"}))
    fakes = Fakes(monkeypatch, tmp_path)
    out = verify.run(inp)
    assert out["status"] == "fail"
    assert out["reason"] == "decided by Oleg: stop: not worth it"
    assert fakes.writes == []


def test_findings_name_the_offending_tests_and_the_surviving_mutants(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("def f(x):\n    return sorted(x, reverse=True)\n")
    ctx = verify._context(_inp(tmp_path))
    revert_json = tmp_path / "revert.json"
    revert_json.write_text(json.dumps({"status": "fail", "result": FAILED_REPORT["revert"]}))
    text = verify._findings(ctx, {"check": "revert", "reason": "revert check: x", "report": str(revert_json)})
    assert "tests/test_x.py::test_x: missing-name (at head: pass, without the change: missing-name)" in text
    assert "No test fails on an assertion" in text
    gen = {
        "on_changed_lines": {"checked": 2, "killed": 0, "survived": 2},
        "mutants": {
            "pkg.mod.x_f__mutmut_1": {"status": "survived", "line": 2, "changed_line": True},
            "pkg.mod.x_f__mutmut_2": {"status": "killed", "line": 2, "changed_line": True},
        },
    }
    mutation_json = tmp_path / "mutation.json"
    mutation_json.write_text(
        json.dumps({"status": "fail", "result": {"only_mutate": ["pkg/mod.py"], "runs": {"generated": gen}}})
    )
    text = verify._findings(
        ctx, {"check": "mutation", "reason": "kill no mutant", "report": str(mutation_json)}
    )
    assert "on the changed lines: checked 2, killed 0, survived 2" in text
    assert text.count("line 2: return sorted(x, reverse=True)") == 1


def test_the_developers_mutation_set_runs_once_per_verify_run(tmp_path, monkeypatch):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("def f(x):\n    return x\n")
    source = tmp_path / "source.json"
    source.write_text(json.dumps([{"path": "pkg/mod.py", "status": "M"}]))
    tests = tmp_path / "tests.json"
    tests.write_text(json.dumps([{"path": "tests/test_dev.py", "status": "A"}]))
    inp = _inp(tmp_path, artifacts={"changed_source": str(source), "changed_tests": str(tests)})
    inp["repo"]["app"].update(
        source_package="pkg",
        api_tests_dir="tests",
        python="python",
        exclude_copy=[],
        mutmut={"pytest_add_cli_args": [], "pre_create_dirs": []},
    )
    runs = []

    def fake_run(tree, python, pkg, only, files, globs, workdir, *rest):
        runs.append(os.path.basename(workdir))
        return {"status": "pass", "generated": 2, "checked": 2, "killed": 2, "on_changed_lines": {}}

    monkeypatch.setattr(verify.mutants, "changed_functions", lambda base, head, module: [module + ".x_f*"])
    monkeypatch.setattr(verify.mutants, "changed_lines", lambda base, head: {2})
    monkeypatch.setattr(verify.mutants, "run", fake_run)
    ctx = verify._context(inp)
    ctx["files"] = ["tests/test_x.py"]
    first, second = verify.run_mutation(ctx), verify.run_mutation(ctx)
    assert runs.count("generated") == 2 and runs.count("developers") == 1
    assert second["runs"]["developers"]["test_files"] == ["tests/test_dev.py"]
    assert first["runs"]["developers"] is second["runs"]["developers"]


# ------------------------------------------------------------------ the writer in real git trees
def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env
    ).stdout


@pytest.fixture
def trees(tmp_path):
    """One repository, its base and head commits checked out as the ticket's two worktrees."""
    src = tmp_path / "src"
    (src / "tests").mkdir(parents=True)
    git(src, "init", "-q")
    (src / "app.py").write_text("def add(a, b):\n    return a - b\n")
    (src / "tests" / "test_old.py").write_text("def test_old():\n    assert True\n")
    git(src, "add", ".")
    git(src, "commit", "-q", "-m", "base")
    base = git(src, "rev-parse", "HEAD").strip()
    (src / "app.py").write_text("def add(a, b):\n    return a + b\n")
    (src / "e2e").mkdir()
    (src / "e2e" / "e2e_test_old.py").write_text("def test_x():\n    assert True\n")
    git(src, "add", ".")
    git(src, "commit", "-q", "-m", "head")
    head = git(src, "rev-parse", "HEAD").strip()
    wt = tmp_path / "wt"
    git(src, "worktree", "add", "-q", "--detach", str(wt / "demo-x" / "base"), base)
    git(src, "worktree", "add", "-q", "--detach", str(wt / "demo-x" / "head"), head)
    diff = tmp_path / "change.diff"
    diff.write_text("DIFF-MARKER")
    strategy = tmp_path / "strategy.md"
    strategy.write_text("STRATEGY")
    app = {
        "name": "demo",
        "repo": str(src),
        "worktrees": str(wt),
        "strategy": str(strategy),
        "api_tests_dir": "tests",
        "browser_tests_dir": "e2e",
        "browser_test_files": "e2e_test_*.py",
        "python": "python",
    }
    return {
        "repo": {
            "app": app,
            "base": base,
            "head": head,
            "base_tree": str(wt / "demo-x" / "base"),
            "head_tree": str(wt / "demo-x" / "head"),
        },
        "ticket": {"id": "demo-x", "title": "x", "qa_mode": "blind", "base": base, "head": head},
        "artifacts": {"change_diff": str(diff)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


class FakeClaude:
    """verify.RUNNER: writes or edits tests/test_x_api.py in its cwd and answers in stream-json."""

    def __init__(self):
        self.calls = []

    def __call__(self, argv, **kwargs):
        cwd = Path(kwargs["cwd"])
        call = {"argv": argv, "cwd": str(cwd), "had_file": (cwd / "tests" / "test_x_api.py").exists()}
        if "--settings" in argv:
            call["settings"] = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
        self.calls.append(call)
        (cwd / "tests" / "test_x_api.py").write_text(f"def test_x():\n    assert {len(self.calls)}\n")
        tool = {"type": "tool_use", "name": "Write", "input": {"file_path": "tests/test_x_api.py"}}
        result = {
            "type": "result",
            "is_error": False,
            "result": "",
            "structured_output": {"files": ["tests/test_x_api.py"], "notes": "n"},
            "total_cost_usd": 0.75,
            "modelUsage": {"claude-test": {}},
        }
        lines = [{"type": "assistant", "message": {"content": [tool]}}, result]
        return subprocess.CompletedProcess(argv, 0, "\n".join(json.dumps(x) for x in lines), "")


def test_the_blind_writer_works_in_the_base_tree_and_its_repair_in_the_head_tree(trees, monkeypatch):
    claude = FakeClaude()
    monkeypatch.setattr(verify, "RUNNER", claude)
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", verify.write_tests)])
    base, head = Path(trees["repo"]["base_tree"]), Path(trees["repo"]["head_tree"])
    ctx = verify._context(trees)

    assert verify._attempt(ctx, "write") is None
    blind_call = claude.calls[0]
    assert blind_call["cwd"] == str(base)
    assert "stream-json" in blind_call["argv"]
    deny = blind_call["settings"]["permissions"]["deny"]
    assert "Bash(git *)" in deny and f"Read(/{head.resolve()}/**)" in deny
    prompt = blind_call["argv"][2]
    assert "DIFF-MARKER" not in prompt and trees["ticket"]["head"] not in prompt
    assert "e2e_test_old" not in prompt  # no developers' tests
    assert (head / "tests" / "test_x_api.py").is_file()
    assert not (base / "tests" / "test_x_api.py").exists()
    assert git(base, "status", "--porcelain") == ""
    manifest = json.loads((Path(ctx["out"]) / "rounds" / "1" / "tests_manifest.json").read_text())
    assert manifest["files"] == ["tests/test_x_api.py"]
    assert manifest["blind_audit"]["tool_calls"] == 1 and manifest["blind_audit"]["clean"] is True
    assert _ledger_kinds_of(trees) == [("write", 0.75)]

    assert verify._attempt(ctx, "repair", findings="FINDINGS-MARKER") is None
    repair_call = claude.calls[1]
    assert repair_call["cwd"] == str(head) and repair_call["had_file"]  # the folders were not cleaned
    assert "stream-json" not in repair_call["argv"]
    assert "Bash(git *)" not in repair_call["settings"]["permissions"]["deny"]
    prompt = repair_call["argv"][2]
    assert "FINDINGS-MARKER" in prompt and "Its diff is not given" in prompt and "DIFF-MARKER" not in prompt
    assert (head / "tests" / "test_x_api.py").read_text().endswith("assert 2\n")
    copy = Path(ctx["out"]) / "rounds" / "2" / "tests" / "tests" / "test_x_api.py"
    assert copy.read_text().endswith("assert 2\n")
    assert (Path(ctx["out"]) / "tests" / "tests" / "test_x_api.py").read_text().endswith("assert 2\n")
    report = _report_of(trees)
    assert report["blind"] is True and report["blind_audit"]["clean"] is True


def test_the_sequential_writer_works_in_the_head_tree_with_the_diff(trees, monkeypatch):
    claude = FakeClaude()
    monkeypatch.setattr(verify, "RUNNER", claude)
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", verify.write_tests)])
    del trees["ticket"]["qa_mode"]
    head = Path(trees["repo"]["head_tree"])
    (head / "tests" / "leftover.py").write_text("x = 1\n")  # an earlier round's file is cleaned first
    ctx = verify._context(trees)
    assert verify._attempt(ctx, "write") is None
    call = claude.calls[0]
    assert call["cwd"] == str(head) and "stream-json" not in call["argv"]
    assert "DIFF-MARKER" in call["argv"][2] and "e2e_test_old" in call["argv"][2]
    assert "Bash(git *)" not in call["settings"]["permissions"]["deny"]
    assert ctx["files"] == ["tests/test_x_api.py"] and not (head / "tests" / "leftover.py").exists()


def _ledger_kinds_of(inp):
    saved = json.loads((Path(inp["run_dir"]) / "rounds.json").read_text())
    return [(e["kind"], e["cost_usd"]) for e in saved["entries"]]


def _report_of(inp):
    return json.loads((Path(inp["run_dir"]) / "verify" / "report.json").read_text())


# ------------------------------------------------------------------ the review's fix round
def _verified(tmp_path):
    """Review's input after a Verify run: the tests copied to the run folder, gone from the head tree."""
    head = tmp_path / "head"
    head.mkdir()
    copy = tmp_path / "run" / "verify" / "tests"
    (copy / "tests").mkdir(parents=True)
    (copy / "tests" / "test_x.py").write_text("def test_x():\n    assert 1\n")
    manifest = tmp_path / "run" / "verify" / "tests_manifest.json"
    manifest.write_text(json.dumps({"files": ["tests/test_x.py"]}))
    inp = _inp(tmp_path, artifacts={"tests_manifest": str(manifest), "tests_dir": str(copy)})
    inp["repo"]["head_tree"] = str(head)
    return inp, head


REVIEW = {
    "verdict": "request_changes",
    "findings": [
        {"file": "tests/test_x.py", "line": 2, "severity": "high", "summary": "weak", "failure_scenario": "S"}
    ],
}


def test_repair_from_review_runs_one_fix_round_then_the_cases_and_the_approval(tmp_path, monkeypatch):
    inp, head = _verified(tmp_path)
    fakes = Fakes(monkeypatch, tmp_path)
    out = verify.repair_from_review(inp, REVIEW)
    assert out["status"] == "pass", out["reason"]
    assert (head / "tests" / "test_x.py").is_file()
    assert fakes.writes[0]["files"] == ["tests/test_x.py"]
    assert fakes.writes[0]["kind"] == "review_fix" and fakes.writes[0]["mode"] == "repair"
    assert "tests/test_x.py:2 high weak: S" in fakes.writes[0]["findings"]
    assert fakes.cases == 1
    approval = json.loads(Path(out["artifacts"]["approval"]).read_text())
    assert approval["rule"] == "every check passed after the review's fix round"
    assert _ledger_kinds(tmp_path) == ["review_fix"]


def test_repair_from_review_asks_a_person_when_the_ticket_says_so(tmp_path, monkeypatch):
    inp, _ = _verified(tmp_path)
    inp["ticket"]["gate"] = "person"
    Fakes(monkeypatch, tmp_path)
    assert verify.repair_from_review(inp, REVIEW)["status"] == "needs_person"
    assert _report(tmp_path)["gate_kind"] == "approval"


def test_repair_from_review_without_a_writer_round_left_calls_nothing(tmp_path, monkeypatch):
    inp, _ = _verified(tmp_path)
    inp["ticket"]["caps"] = {"writer_rounds": 0}
    fakes = Fakes(monkeypatch, tmp_path)
    out = verify.repair_from_review(inp, REVIEW)
    assert out["status"] == "fail" and "no writer round left" in out["reason"]
    assert fakes.writes == [] and fakes.cases == 0


def test_the_report_says_how_the_step_ended(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path)
    assert verify.run(_inp(tmp_path))["status"] == "pass"
    assert _report(tmp_path)["status"] == "pass"


def test_a_failed_step_and_a_declined_approval_leave_the_report_failed(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    Advisor(monkeypatch, "environment")
    assert verify.run(_inp(tmp_path))["status"] == "fail"
    assert _report(tmp_path)["status"] == "fail"

    other = tmp_path / "other"
    other.mkdir()
    Fakes(monkeypatch, other)
    inp = _inp(other, {"gate": "person"})
    assert verify.run(inp)["status"] == "needs_person"
    assert _report(other)["status"] == "needs_person"
    answer = other / "run" / "answer.json"
    answer.write_text(json.dumps({"approved": False, "by": "Oleg", "note": "no"}))
    assert verify.run({**inp, "artifacts": {"answer": str(answer)}})["status"] == "fail"
    assert _report(other)["status"] == "fail"


def test_an_escalation_answer_that_is_not_retry_leaves_the_report_failed(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    answer.write_text(json.dumps({"decision": "change_is_wrong", "note": "n", "by": "Oleg"}))
    assert verify.run(inp)["status"] == "fail"
    assert _report(tmp_path)["status"] == "fail"


def test_the_test_cases_of_an_earlier_round_never_stay_beside_the_new_ones(tmp_path, monkeypatch):
    inp = _inp(tmp_path)
    inp["repo"]["app"]["source_package"] = "demo"
    ctx = verify._context(inp)
    stale = Path(ctx["out"]) / "testcases" / "demo" / "TC-demo-009.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("a case for a test that no longer exists")
    ctx["files"] = []

    def fake_claude(argv, **kwargs):
        raw = {"structured_output": {"files": []}, "is_error": False, "total_cost_usd": 0.1}
        return subprocess.CompletedProcess(argv, 0, json.dumps(raw), "")

    monkeypatch.setattr(verify, "RUNNER", fake_claude)
    try:
        verify.write_cases(ctx)
    except verify.CheckFailed:
        pass  # no case was written; what matters is that the stale one is gone
    assert not stale.exists()


def test_files_changed_before_the_writer_ran_are_not_blamed_on_it_nor_undone(trees, monkeypatch):
    # fetch.py's npm install rewrote linkding's package-lock.json at 573b6f5 before any writer ran.
    claude = FakeClaude()
    monkeypatch.setattr(verify, "RUNNER", claude)
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", verify.write_tests)])
    del trees["ticket"]["qa_mode"]
    head = Path(trees["repo"]["head_tree"])
    (head / "app.py").write_text("def add(a, b):\n    return a + b  # prepared\n")
    (head / "build.log").write_text("made by the preparation\n")
    ctx = verify._context(trees)
    assert verify._attempt(ctx, "write") is None
    assert verify._attempt(ctx, "repair", findings="F") is None
    assert (head / "app.py").read_text().endswith("# prepared\n")
    assert (head / "build.log").exists()


def test_a_writer_change_to_an_already_changed_file_is_undone_back_to_what_was_there(trees, monkeypatch):
    claude = FakeClaude()

    def edits_app(argv, **kwargs):
        (Path(kwargs["cwd"]) / "app.py").write_text("def add(a, b):\n    return 0\n")
        return claude(argv, **kwargs)

    monkeypatch.setattr(verify, "RUNNER", edits_app)
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", verify.write_tests)])
    del trees["ticket"]["qa_mode"]
    head = Path(trees["repo"]["head_tree"])
    prepared = "def add(a, b):\n    return a + b  # prepared\n"
    (head / "app.py").write_text(prepared)
    failure = verify._attempt(verify._context(trees), "write")
    assert failure["check"] == "write_tests" and "app.py" in failure["reason"]
    assert (head / "app.py").read_text() == prepared


def test_the_writer_may_not_make_worktrees_or_run_npm(trees, monkeypatch):
    claude = FakeClaude()
    monkeypatch.setattr(verify, "RUNNER", claude)
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", verify.write_tests)])
    del trees["ticket"]["qa_mode"]
    verify._attempt(verify._context(trees), "write")
    deny = claude.calls[0]["settings"]["permissions"]["deny"]
    assert "Bash(git worktree*)" in deny and "Bash(npm *)" in deny


def test_too_little_left_for_the_stronger_model_fails_the_step_instead_of_asking(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, "cannot_decide")
    out = verify.run(_inp(tmp_path, {"caps": {"usd": 1.75}}))  # the writer's 0.5 leaves 1.25 < 1.50
    assert out["status"] == "fail" and "spend cap reached" in out["reason"]
    assert advisor.calls == []


def _round_with_tests(tmp_path, n, body):
    folder = tmp_path / "run" / "verify" / "rounds" / str(n)
    (folder / "tests" / "tests").mkdir(parents=True, exist_ok=True)
    (folder / "tests" / "tests" / "test_x.py").write_text(body)
    (folder / "tests_manifest.json").write_text(json.dumps({"files": ["tests/test_x.py"]}))


def test_a_recheck_answer_judges_an_earlier_rounds_tests_again_without_a_writer(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    _round_with_tests(tmp_path, 1, "def test_x():\n    assert 'round one'\n")
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    assert 'a later repair'\n")
    answer.write_text(json.dumps({"decision": "recheck", "round": 1, "by": "the session"}))
    fakes = Fakes(monkeypatch, tmp_path)
    cleaned = []
    monkeypatch.setattr(verify, "_clean_tests", lambda tree, app: cleaned.append(tree))  # no git here
    out = verify.run(inp)
    assert out["status"] == "pass", out["reason"]
    assert fakes.writes == []  # no writer call
    assert cleaned == [str(tmp_path)]  # the later round's files are cleared first
    assert (tmp_path / "tests" / "test_x.py").read_text().endswith("'round one'\n")
    report = _report(tmp_path)
    assert [(r["round"], r["kind"]) for r in report["rounds"]] == [(1, "write"), (2, "recheck")]
    manifest = json.loads((tmp_path / "run" / "verify" / "rounds" / "2" / "tests_manifest.json").read_text())
    assert manifest["rechecked_round"] == 1 and manifest["files"] == ["tests/test_x.py"]
    assert _ledger_kinds(tmp_path) == ["write", "advice"]  # a recheck spends nothing


def test_a_recheck_of_a_round_that_kept_no_tests_goes_to_the_stronger_model(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    answer.write_text(json.dumps({"decision": "recheck", "round": 7, "by": "the session"}))
    Fakes(monkeypatch, tmp_path)
    advisor = Advisor(monkeypatch, "environment")
    out = verify.run(inp)
    assert out["status"] == "fail" and "environment problem" in out["reason"]
    assert advisor.calls[0]["failure"]["reason"] == "round 7 kept no tests to check again"


def test_a_recheck_never_takes_a_round_whose_tests_failed_the_writers_own_checks(tmp_path, monkeypatch):
    inp, answer = _escalated(tmp_path, monkeypatch)
    _round_with_tests(tmp_path, 1, "def test_x():\n    assert 1\n")
    written = tmp_path / "run" / "verify" / "rounds" / "1" / "write_tests.json"
    written.write_text(json.dumps({"status": "fail", "reason": "test writer wrote no API test file"}))
    answer.write_text(json.dumps({"decision": "recheck", "round": 1, "by": "the session"}))
    Fakes(monkeypatch, tmp_path)
    advisor = Advisor(monkeypatch, "environment")
    out = verify.run(inp)
    assert out["status"] == "fail"
    assert (
        "failed the writer's own checks: test writer wrote no API test file"
        in (advisor.calls[0]["failure"]["reason"])
    )


@pytest.mark.parametrize("given", [None, "latest", 0, True])
def test_a_recheck_answer_needs_a_round_number(tmp_path, monkeypatch, given):
    inp, answer = _escalated(tmp_path, monkeypatch)
    answer.write_text(json.dumps({"decision": "recheck", "round": given, "by": "Oleg"}))
    fakes = Fakes(monkeypatch, tmp_path)
    out = verify.run(inp)
    assert out["status"] == "fail" and "recheck without a round number" in out["reason"]
    assert fakes.writes == [] and fakes.calls == {}


def test_status_reads_paths_with_spaces_unquoted(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a b.txt").write_text("one\n")
    (tmp_path / "old name.txt").write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "c")
    (tmp_path / "a b.txt").write_text("two\n")
    (tmp_path / "née.py").write_text("x = 1\n")
    git(tmp_path, "mv", "old name.txt", "new name.txt")
    assert sorted(verify._status(str(tmp_path))) == [
        (" M", "a b.txt"),
        ("??", "née.py"),
        ("R ", "new name.txt"),
    ]


def test_a_lowered_advice_budget_still_reaches_the_stronger_model(tmp_path, monkeypatch):
    Fakes(monkeypatch, tmp_path, suite=["fail"])
    advisor = Advisor(monkeypatch, "environment")
    monkeypatch.setattr(verify.escalate, "BUDGET_USD", 1.0)
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "fail" and "environment problem" in out["reason"]
    assert advisor.calls[0]["budget_usd"] == 1.0
