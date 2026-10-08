import sys

from factory.checks import suite


def _tree(tmp_path, failing: bool):
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    if failing:
        (tmp_path / "test_bad.py").write_text("def test_bad():\n    assert False\n")
    return tmp_path


def test_failing_file_fails_the_suite(tmp_path):
    tree = _tree(tmp_path, failing=True)
    result = suite.run(tree, sys.executable, [["test_ok.py"], ["test_bad.py"]], ["-p", "no:cacheprovider"])
    assert result["status"] == "fail"
    assert [r["returncode"] for r in result["runs"]] == [0, 1]
    assert "1 passed" in result["runs"][0]["summary"]
    assert "1 failed" in result["runs"][1]["summary"]
    assert result["runs"][1]["tail"]


def test_passing_only_passes(tmp_path):
    tree = _tree(tmp_path, failing=False)
    result = suite.run(tree, sys.executable, [["test_ok.py"]], ["-p", "no:cacheprovider"])
    assert result["status"] == "pass"
    assert result["runs"][0]["wall_s"] >= 0
