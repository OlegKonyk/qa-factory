"""The parts of the Verify step that run without a model or an application."""

import json
import subprocess

import pytest

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


def test_the_new_answer_form_approves_and_declines(tmp_path):
    out, report = _report(tmp_path)
    answer = tmp_path / "run" / "answer.json"
    inp = {
        "repo": {"app": {"name": "demo"}, "head_tree": "", "base_tree": ""},
        "ticket": {"id": "demo-x", "title": "x"},
        "artifacts": {"answer": str(answer)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }
    answer.write_text(json.dumps({"decision": "approve", "by": "Dana", "note": "fine"}))
    result = verify.run(inp)
    assert result["status"] == "pass" and result["reason"] == "approved by Dana: fine"
    answer.write_text(json.dumps({"decision": "decline", "by": "Dana", "note": "weak"}))
    result = verify.run(inp)
    assert result["status"] == "fail" and result["reason"] == "declined by Dana: weak"


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
        "api_helpers": "a/helpers.py",
        "browser_tests_dir": "b",
        "api_test_file": "c",
        "browser_test_file": "d",
        "browser_glob": "e",
        "python": "f",
    }
    assert "test_sort" not in verify._prompt("write_tests", values)
    blind_values = {k: v for k, v in values.items() if k not in ("diff", "dev_tests_diff")}
    blind_prompt = verify._prompt("write_tests_blind", blind_values)
    assert "before the change" in blind_prompt and "{" not in blind_prompt.replace("{}", "")
    repair_values = {k: v for k, v in blind_values.items() if k != "plan_json"}
    repair_values.update(change_section="CHANGE", files="F", findings="FINDINGS", guidance="G")
    repair = verify._prompt("write_tests_repair", repair_values)
    assert "FINDINGS" in repair and "CHANGE" in repair and "{" not in repair.replace("{}", "")
    cases = verify._prompt(
        "test_cases", {"ticket_json": "{}", "tests_listing": "- x", "area": "bookmarks", "out_dir": "/o"}
    )
    assert "TC-bookmarks-001" in cases


def _fake_checks(monkeypatch):
    """Every check passes with the minimal result the end of Verify reads."""

    def write_tests(ctx):
        ctx["files"] = ["tests/test_x.py"]
        return {"files": ctx["files"]}

    results = {
        "lint": lambda ctx: {"status": "pass", "findings": []},
        "revert": lambda ctx: {
            "status": "pass",
            "tests": {"tests/test_x.py::test_x": {"verdict": "proves-behaviour"}},
        },
        "mutation": lambda ctx: {"skipped": "no function changed"},
        "suite": lambda ctx: {"status": "pass", "runs": [{"summary": "1 passed"}]},
    }
    monkeypatch.setattr(verify, "ATTEMPT_CHECKS", [("write_tests", write_tests)] + list(results.items()))
    monkeypatch.setattr(
        verify, "FINAL_CHECKS", [("test_cases", lambda ctx: {"files": ["demo/TC-demo-001.md"]})]
    )


def _inp(tmp_path, ticket_extra=None):
    ticket = {"id": "demo-x", "title": "x", **(ticket_extra or {})}
    return {
        "repo": {"app": {"name": "demo"}, "head_tree": str(tmp_path), "base_tree": str(tmp_path)},
        "ticket": ticket,
        "artifacts": {},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


def test_verify_passes_without_asking_when_every_check_passes(tmp_path, monkeypatch):
    _fake_checks(monkeypatch)
    out = verify.run(_inp(tmp_path))
    assert out["status"] == "pass", out["reason"]
    assert out["gate"] is None
    approval = json.load(open(out["artifacts"]["approval"]))
    assert approval["by"] == "factory" and approval["approved"] is True


def test_a_ticket_can_still_ask_for_a_person(tmp_path, monkeypatch):
    _fake_checks(monkeypatch)
    out = verify.run(_inp(tmp_path, {"gate": "person"}))
    assert out["status"] == "needs_person"
    assert out["gate"]["who"] == "Oleg"
    assert out["gate"]["kind"] == "approval"
    assert [a["decision"] for a in out["gate"]["answers"]] == ["approve", "decline"]
    assert all(a["means"] for a in out["gate"]["answers"])


def test_gates_verify_person_stops_and_the_recipe_names_who_is_asked(tmp_path, monkeypatch):
    _fake_checks(monkeypatch)
    inp = _inp(tmp_path, {"gates": {"verify": "person"}})
    inp["repo"]["app"]["approver"] = "Dana"
    out = verify.run(inp)
    assert out["status"] == "needs_person" and out["gate"]["who"] == "Dana"


@pytest.mark.parametrize("mode", ["auto", "model"])
def test_auto_and_model_approve_passing_work(tmp_path, monkeypatch, mode):
    _fake_checks(monkeypatch)
    out = verify.run(_inp(tmp_path, {"gates": {"verify": mode}, "gate": "person"}))
    assert out["status"] == "pass" and out["gate"] is None


def _writer_ctx(tmp_path, app_extra, mode, blind):
    strategy = tmp_path / "strategy.md"
    strategy.write_text("STRATEGY")
    app = {
        "api_tests_dir": "tests",
        "python": "py",
        "strategy": str(strategy),
        **app_extra,
    }
    return {
        "app": app,
        "head_tree": str(tmp_path),
        "slug": "sort",
        "ticket": {"id": "t", "title": "sort"},
        "artifacts": {},
        "mode": mode,
        "blind": blind,
        "files": ["tests/test_sort_api.py"],
        "findings": "F",
        "guidance": "G",
        "repo": {"base": "b", "head": "h"},
    }


@pytest.mark.parametrize(
    "mode,blind",
    [("fresh", False), ("fresh", True), ("repair", False), ("repair", True)],
)
def test_writer_prompt_without_browser_keys_asks_for_api_tests_only(tmp_path, monkeypatch, mode, blind):
    monkeypatch.setattr(verify, "_git", lambda *a, **k: "")
    prompt = verify._writer_prompt(_writer_ctx(tmp_path, {}, mode, blind))
    assert "API tests only" in prompt
    assert "{browser" not in prompt and "None" not in prompt
    assert "browser_" not in prompt and "e2e" not in prompt


@pytest.mark.parametrize("mode,blind", [("fresh", False), ("fresh", True), ("repair", False)])
def test_writer_prompt_with_browser_keys_keeps_the_browser_instructions(tmp_path, monkeypatch, mode, blind):
    monkeypatch.setattr(verify, "_git", lambda *a, **k: "")
    extra = {"browser_tests_dir": "e2e", "browser_test_files": "e2e_test_*.py"}
    prompt = verify._writer_prompt(_writer_ctx(tmp_path, extra, mode, blind))
    assert "API tests only" not in prompt
    assert "e2e/e2e_test_sort.py" in prompt and "python_files=e2e_test_*.py" in prompt
    assert "{browser" not in prompt and "None" not in prompt


@pytest.mark.parametrize("mode,blind", [("fresh", False), ("fresh", True)])
def test_writer_prompt_names_the_recipe_helper_file_or_helpers_py(tmp_path, monkeypatch, mode, blind):
    monkeypatch.setattr(verify, "_git", lambda *a, **k: "")
    default = verify._writer_prompt(_writer_ctx(tmp_path, {}, mode, blind))
    assert "Read `tests/helpers.py`" in default
    named = verify._writer_prompt(_writer_ctx(tmp_path, {"test_helpers": "tests/fixtures.py"}, mode, blind))
    assert "Read `tests/fixtures.py`" in named and "tests/helpers.py" not in named


def test_a_recipe_without_browser_keys_touches_only_the_api_folder(tmp_path):
    app = {"api_tests_dir": "tests", "browser_tests_dir": None}
    assert verify.browser_dir(app) is None and verify.browser_dir({"api_tests_dir": "tests"}) is None
    assert verify._in_test_dirs("tests/test_x.py", app)
    assert not verify._in_test_dirs("e2e/e2e_test_x.py", app)
    tree = tmp_path / "tree"
    tree.mkdir()
    for cmd in (["init", "-q"],):
        subprocess.run(["git", "-C", str(tree), *cmd], check=True)
    (tree / "tests").mkdir()
    (tree / "e2e").mkdir()
    (tree / "tests" / "test_new.py").write_text("x = 1\n")
    (tree / "e2e" / "keep.py").write_text("x = 1\n")
    verify._clean_tests(str(tree), {"api_tests_dir": "tests"})
    assert not (tree / "tests" / "test_new.py").exists()
    assert (tree / "e2e" / "keep.py").exists()
