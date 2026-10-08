"""The parts of the Verify step that run without a model or an application."""

import json

from factory.steps import verify


def test_test_ids_lists_methods_and_functions(tmp_path):
    (tmp_path / "test_a.py").write_text(
        "class ATestCase:\n"
        "    def test_one(self):\n        pass\n"
        "    def helper(self):\n        pass\n"
        "def test_two():\n    pass\n"
        "def not_a_test():\n    pass\n"
    )
    assert verify._test_ids(str(tmp_path), "test_a.py") == [
        "test_a.py::ATestCase::test_one",
        "test_a.py::test_two",
    ]


def test_test_ids_survives_a_syntax_error(tmp_path):
    (tmp_path / "test_bad.py").write_text("def (:\n")
    assert verify._test_ids(str(tmp_path), "test_bad.py") == []


def _report(tmp_path):
    out = tmp_path / "run" / "verify"
    out.mkdir(parents=True)
    report = out / "report.json"
    report.write_text(json.dumps({"artifacts": {"tests_manifest": "m.json"}, "metrics": {"cost_usd": 1.5}}))
    return out, report


def test_an_approval_passes_the_step_without_redoing_the_checks(tmp_path):
    out, report = _report(tmp_path)
    answer = tmp_path / "run" / "answer.json"
    answer.write_text(json.dumps({"approved": True, "by": "Oleg", "note": "fine"}))
    inp = {
        "repo": {"app": {"name": "demo"}, "head_tree": "", "base_tree": ""},
        "ticket": {"id": "demo-x", "title": "x"},
        "artifacts": {"answer": str(answer)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }
    result = verify.run(inp)
    assert result["status"] == "pass"
    assert result["artifacts"] == {"tests_manifest": "m.json"}
    assert "approved by Oleg" in result["reason"]
    assert result["metrics"]["cost_usd"] == 1.5


def test_a_refusal_fails_the_step(tmp_path):
    out, report = _report(tmp_path)
    answer = tmp_path / "run" / "answer.json"
    answer.write_text(json.dumps({"approved": False, "by": "Oleg", "note": "the browser test is weak"}))
    inp = {
        "repo": {"app": {"name": "demo"}, "head_tree": "", "base_tree": ""},
        "ticket": {"id": "demo-x", "title": "x"},
        "artifacts": {"answer": str(answer)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }
    result = verify.run(inp)
    assert result["status"] == "fail"
    assert "the browser test is weak" in result["reason"]


def test_prompts_have_every_placeholder_the_step_fills():
    values = {
        "ticket_json": "{}",
        "strategy": "",
        "diff": "",
        "dev_tests_diff": "",
        "plan_json": "",
        "api_tests_dir": "a",
        "browser_tests_dir": "b",
        "api_test_file": "c",
        "browser_test_file": "d",
        "browser_glob": "e",
        "python": "f",
    }
    assert "test_sort" not in verify._prompt("write_tests", values)
    cases = verify._prompt(
        "test_cases", {"ticket_json": "{}", "tests_listing": "- x", "area": "bookmarks", "out_dir": "/o"}
    )
    assert "TC-bookmarks-001" in cases
