"""Tests for the lint check, run with the factory's own interpreter (ruff is in its environment)."""

import sys
from pathlib import Path

import pytest

from factory.checks import lint

SOURCE = """\
import time
import unittest
from unittest import mock


def test_nothing_checked():
    x = 1 + 1
    print(x)


class ThingTest(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(1 + 1, 2)


def test_visible(page):
    expect(page.locator("h1")).to_be_visible()  # noqa: F821


def test_sleeps():
    time.sleep(1)
    assert True


def test_raises():
    with pytest.raises(ZeroDivisionError):  # noqa: F821
        print(1 / 0)


@mock.patch("bookmarks.services.tasks.load_favicon")
def test_patches_own_code(load_favicon):
    assert load_favicon is not None
"""


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_gen.py").write_text(SOURCE)
    return tmp_path


def rules_for(findings, line=None):
    return {f["rule"] for f in findings if line is None or f["line"] == line}


def line_of(text):
    return SOURCE.splitlines().index(text) + 1


def test_a_test_without_assertions_is_flagged(tree):
    report = lint.run(tree, sys.executable, ["tests/test_gen.py"])

    assert report["status"] == "fail"
    assert "no-assertion" in rules_for(report["findings"], line_of("def test_nothing_checked():"))


@pytest.mark.parametrize(
    "definition",
    [
        "    def test_equal(self):",
        "def test_visible(page):",
        "def test_sleeps():",
        "def test_raises():",
    ],
)
def test_tests_that_assert_are_not_flagged(tree, definition):
    report = lint.run(tree, sys.executable, ["tests/test_gen.py"])

    assert "no-assertion" not in rules_for(report["findings"], line_of(definition))


def test_time_sleep_is_flagged(tree):
    report = lint.run(tree, sys.executable, ["tests/test_gen.py"])

    assert "sleep" in rules_for(report["findings"], line_of("    time.sleep(1)"))


def test_patching_the_applications_own_code_is_flagged_only_when_the_package_is_given(tree):
    without = lint.run(tree, sys.executable, ["tests/test_gen.py"])
    given = lint.run(tree, sys.executable, ["tests/test_gen.py"], app_package="bookmarks")

    assert "mocks-own-code" not in rules_for(without["findings"])
    assert "mocks-own-code" in rules_for(given["findings"])


def test_ruff_findings_come_through_with_file_and_line(tree):
    (tree / "tests" / "test_unused.py").write_text("import os\n\n\ndef test_ok():\n    assert True\n")

    report = lint.run(tree, sys.executable, ["tests/test_unused.py"])

    assert {"file": "tests/test_unused.py", "line": 1, "rule": "F401"} == {
        k: report["findings"][0][k] for k in ("file", "line", "rule")
    }


def test_unformatted_file_is_flagged(tree):
    (tree / "tests" / "test_ugly.py").write_text("def test_ok( ):\n    assert   True\n")

    report = lint.run(tree, sys.executable, ["tests/test_ugly.py"])

    assert rules_for(report["findings"]) == {"format"}
    assert report["findings"][0]["file"] == "tests/test_ugly.py"


def test_a_clean_file_passes(tree):
    (tree / "tests" / "test_clean.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")

    assert lint.run(tree, sys.executable, ["tests/test_clean.py"]) == {"status": "pass", "findings": []}


def test_files_under_excluded_directories_are_skipped(tree):
    report = lint.run(tree, sys.executable, ["tests/test_gen.py"], exclude_dirs=["tests"])

    assert report == {"status": "pass", "findings": []}


LINKDING_PYTHON = Path("~/Library/Caches/qa-factory/linkding/repo/.venv/bin/python").expanduser()


@pytest.mark.linkding
@pytest.mark.skipif(not LINKDING_PYTHON.exists(), reason="the linkding clone is absent")
def test_the_applications_older_ruff_output_is_understood(tree):
    (tree / "tests" / "test_ugly.py").write_text("import os\ndef test_ok( ):\n    assert   True\n")

    report = lint.run(tree, str(LINKDING_PYTHON), ["tests/test_ugly.py"])

    assert rules_for(report["findings"]) == {"F401", "format"}
    assert not (tree / ".ruff_cache").exists()


@pytest.mark.skipif(not Path("/usr/bin/python3").exists(), reason="needs the system python without ruff")
def test_a_python_without_ruff_is_a_finding_not_a_pass(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_x():\n    assert True\n")
    report = lint.run(str(tmp_path), "/usr/bin/python3", ["test_x.py"])
    assert report["status"] == "fail"
    assert report["findings"][0]["rule"] == "ruff"
