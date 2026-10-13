"""The revert check on the developers' own tests (factory/checks/devtests.py)."""

import io
import json

from factory.checks import devtests


def _tree(root, body):
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_x.py").write_text(body)
    return root


def test_new_test_ids_are_those_absent_from_the_file_at_base(tmp_path):
    head = _tree(tmp_path / "head", "class T:\n    def test_old(self): pass\n    def test_new(self): pass\n")
    base = _tree(tmp_path / "base", "class T:\n    def test_old(self): pass\n")
    assert devtests.new_test_ids(head, base, "tests/test_x.py", "M") == ["tests/test_x.py::T::test_new"]
    assert devtests.new_test_ids(head, base, "tests/test_x.py", "A") == [
        "tests/test_x.py::T::test_old",
        "tests/test_x.py::T::test_new",
    ]
    assert devtests.new_test_ids(head, base, "tests/missing.py", "M") == []


def test_run_filters_the_revert_report_to_the_new_tests_and_counts_verdicts(tmp_path, monkeypatch):
    head = _tree(tmp_path / "head", "def test_old(): pass\ndef test_a(): pass\ndef test_b(): pass\n")
    base = _tree(tmp_path / "base", "def test_old(): pass\n")
    seen = {}

    def fake_revert(head_tree, base_tree, changed_source, files, *rest):
        seen["files"] = files
        return {
            "status": "fail",
            "reason": "",
            "wall_s": {"head": 1.0, "reverted": 1.0},
            "tests": {
                "tests/test_x.py::test_old": {"at_head": "pass", "verdict": "passes-without-change"},
                "tests/test_x.py::test_a": {"at_head": "pass", "verdict": "proves-behaviour"},
                "tests/test_x.py::test_b": {"at_head": "pass", "verdict": "missing-name"},
            },
        }

    monkeypatch.setattr(devtests.revert, "run", fake_revert)
    changed_tests = [
        {"path": "tests/test_x.py", "status": "M"},
        {"path": "tests/helpers.py", "status": "M"},
        {"path": "tests/snap.json", "status": "A"},
    ]
    support = ["tests/helpers.py"]
    result = devtests.run(head, base, [], changed_tests, tmp_path / "w", "py", [], support, None, [])
    assert seen["files"] == ["tests/test_x.py"]
    assert result["status"] == "ran"
    assert set(result["tests"]) == {"tests/test_x.py::test_a", "tests/test_x.py::test_b"}
    assert result["counts"]["new_tests"] == 2 and result["counts"]["proves-behaviour"] == 1
    assert result["counts"]["missing-name"] == 1 and result["counts"]["passes-without-change"] == 0
    assert "1 of 2 new tests" in result["reason"] and "1 fail only for a missing name" in result["reason"]


def test_run_is_skipped_when_the_change_added_no_test(tmp_path):
    head = _tree(tmp_path / "head", "def test_old(): pass\n")
    base = _tree(tmp_path / "base", "def test_old(): pass\n")
    changed = [{"path": "tests/test_x.py", "status": "M"}]
    result = devtests.run(head, base, [], changed, tmp_path, "py", [], [], None, [])
    assert result["status"] == "skipped" and result["counts"]["new_tests"] == 0


def test_main_runs_from_the_implement_record_and_writes_the_check_file(tmp_path, monkeypatch):
    head = _tree(tmp_path / "head", "def test_a(): pass\n")
    base = _tree(tmp_path / "base", "")
    run = tmp_path / "run"
    (run / "steps").mkdir(parents=True)
    (run / "implement").mkdir()
    (run / "implement" / "changed_source.json").write_text("[]")
    changed = [{"path": "tests/test_x.py", "status": "M"}]
    (run / "implement" / "changed_tests.json").write_text(json.dumps(changed))
    record = {
        "input": {
            "repo": {
                "head_tree": str(head),
                "base_tree": str(base),
                "app": {"python": "py", "pytest_args": [], "test_support": [], "exclude_copy": []},
            }
        },
        "output": {
            "artifacts": {
                "changed_source": str(run / "implement" / "changed_source.json"),
                "changed_tests": str(run / "implement" / "changed_tests.json"),
            }
        },
    }
    (run / "steps" / "03-implement.json").write_text(json.dumps(record))
    monkeypatch.setattr(
        devtests.revert,
        "run",
        lambda *a: {"tests": {"tests/test_x.py::test_a": {"at_head": "pass", "verdict": "proves-behaviour"}}},
    )
    out = io.StringIO()
    assert devtests.main(str(run), out) == 0
    assert "ran: 1 of 1 new tests" in out.getvalue() and "proves-behaviour" in out.getvalue()
    saved = json.loads((run / "verify" / "developers_revert.json").read_text())
    assert saved["status"] == "pass" and saved["result"]["counts"]["proves-behaviour"] == 1
    assert devtests.main(str(tmp_path / "nowhere"), io.StringIO()) == 2
