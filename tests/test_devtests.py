"""The revert check on the developers' own tests (factory/checks/devtests.py)."""

import io
import json

from factory import report
from factory.checks import devtests


def _tree(root, body):
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_x.py").write_text(body)
    return root


def test_judged_test_ids_are_those_absent_from_the_file_at_base(tmp_path):
    head = _tree(tmp_path / "head", "class T:\n    def test_old(self): pass\n    def test_new(self): pass\n")
    base = _tree(tmp_path / "base", "class T:\n    def test_old(self): pass\n")
    assert devtests.judged_test_ids(head, base, "tests/test_x.py", "M") == {
        "tests/test_x.py::T::test_new": "new"
    }
    assert devtests.judged_test_ids(head, base, "tests/test_x.py", "A") == {
        "tests/test_x.py::T::test_old": "new",
        "tests/test_x.py::T::test_new": "new",
    }
    assert devtests.judged_test_ids(head, base, "tests/missing.py", "M") == {}


def test_judged_test_ids_label_modified_tests_and_leave_unchanged_ones_out(tmp_path):
    base = _tree(
        tmp_path / "base",
        "def test_same():\n    assert 1\n"
        "def test_body():\n    assert 1\n"
        "def test_deco():\n    assert 1\n"
        "def test_old_name():\n    assert 1\n",
    )
    head = _tree(
        tmp_path / "head",
        "\n\n# moved down, same function\ndef test_same():\n    assert 1\n"
        "def test_body():\n    assert 2\n"
        "@pytest.mark.slow\ndef test_deco():\n    assert 1\n"
        "def test_new_name():\n    assert 1\n",
    )
    assert devtests.judged_test_ids(head, base, "tests/test_x.py", "M") == {
        "tests/test_x.py::test_body": "modified",
        "tests/test_x.py::test_deco": "modified",
        "tests/test_x.py::test_new_name": "new",
    }


def test_run_filters_the_revert_report_to_the_new_and_modified_tests_and_counts_verdicts(
    tmp_path, monkeypatch
):
    head = _tree(
        tmp_path / "head",
        "def test_old(): pass\ndef test_mod(): assert 2\ndef test_a(): pass\ndef test_b(): pass\n",
    )
    base = _tree(tmp_path / "base", "def test_old(): pass\ndef test_mod(): assert 1\n")
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
                "tests/test_x.py::test_mod": {"at_head": "pass", "verdict": "proves-behaviour"},
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
    assert set(result["tests"]) == {
        "tests/test_x.py::test_a",
        "tests/test_x.py::test_b",
        "tests/test_x.py::test_mod",
    }
    assert result["kinds"] == {
        "tests/test_x.py::test_a": "new",
        "tests/test_x.py::test_b": "new",
        "tests/test_x.py::test_mod": "modified",
    }
    assert result["counts"]["new_tests"] == 2 and result["counts"]["modified_tests"] == 1
    assert result["counts"]["proves-behaviour"] == 2
    assert result["counts"]["missing-name"] == 1 and result["counts"]["passes-without-change"] == 0
    assert result["reason"] == (
        "2 of 3 tests by the developers (2 new, 1 modified) fail on the old code on an assertion; "
        "1 fail only for a missing name"
    )


def test_run_is_skipped_when_the_change_added_or_modified_no_test(tmp_path):
    head = _tree(tmp_path / "head", "def test_old(): pass\n")
    base = _tree(tmp_path / "base", "def test_old(): pass\n")
    changed = [{"path": "tests/test_x.py", "status": "M"}]
    result = devtests.run(head, base, [], changed, tmp_path, "py", [], [], None, [])
    assert result["status"] == "skipped" and result["reason"] == "the change added or modified no test"
    assert result["counts"]["new_tests"] == 0 and result["counts"]["modified_tests"] == 0


def test_main_runs_from_the_implement_record_and_writes_the_check_file(tmp_path, monkeypatch):
    head = _tree(tmp_path / "head", "def test_a(): pass\ndef test_m(): assert 2\n")
    base = _tree(tmp_path / "base", "def test_m(): assert 1\n")
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
        lambda *a: {
            "tests": {
                "tests/test_x.py::test_a": {"at_head": "pass", "verdict": "proves-behaviour"},
                "tests/test_x.py::test_m": {"at_head": "pass", "verdict": "passes-without-change"},
            }
        },
    )
    out = io.StringIO()
    assert devtests.main(str(run), out) == 0
    lines = out.getvalue().splitlines()
    assert lines[0].startswith("ran: 1 of 2 tests by the developers (1 new, 1 modified)")
    assert lines[1].split() == ["proves-behaviour", "new", "tests/test_x.py::test_a"]
    assert lines[2].split() == ["passes-without-change", "modified", "tests/test_x.py::test_m"]
    saved = json.loads((run / "verify" / "developers_revert.json").read_text())
    assert saved["status"] == "pass" and saved["result"]["counts"]["proves-behaviour"] == 1
    assert saved["result"]["kinds"]["tests/test_x.py::test_m"] == "modified"
    table = "\n".join(report._developers_lines(run))
    assert "| test_m | modified |" in table and "| kind |" in table
    assert devtests.main(str(tmp_path / "nowhere"), io.StringIO()) == 2
