"""Tests for the revert check and its failure sorter, on small trees under tmp_path."""

import sys
import textwrap

import pytest

from factory.checks import revert

HEAD_APP = """\
def add(a, b):
    return a + b


def mul(a, b):
    return a * b


def ratio():
    return 4 / 2
"""

BASE_APP = """\
def add(a, b):
    return a - b


def ratio():
    return 4 / 0
"""

TESTS = {
    "test_new.py": "from app import add\n\n\ndef test_add():\n    assert add(2, 2) == 4\n",
    "test_mul.py": "from app import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n",
    "test_ratio.py": "from app import ratio\n\n\ndef test_ratio():\n    assert ratio() == 2\n",
    "test_same.py": "from app import add\n\n\ndef test_add_zero():\n    assert add(3, 0) == 3\n",
    "test_wrong.py": "from app import add\n\n\ndef test_add_wrong():\n    assert add(2, 2) == 5\n",
    "test_unit.py": (
        "import unittest\n\nfrom app import add\n\n\n"
        "class AddTest(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 2), 4)\n"
    ),
}


@pytest.fixture
def trees(tmp_path):
    head, base = tmp_path / "head", tmp_path / "base"
    head.mkdir()
    base.mkdir()
    (head / "app.py").write_text(HEAD_APP)
    (base / "app.py").write_text(BASE_APP)
    for name, body in TESTS.items():
        (head / name).write_text(body)
    return head, base, tmp_path / "work"


def check(trees, files):
    head, base, work = trees
    return revert.run(
        head_tree=head,
        base_tree=base,
        changed_source=[{"path": "app.py", "status": "M"}],
        new_test_files=files,
        workdir=work,
        python=sys.executable,
        pytest_args=["-p", "no:cacheprovider"],
        test_support=[],
        browser_glob="e2e_test_*.py",
        exclude_copy=[".git", "__pycache__"],
    )


def test_a_test_that_fails_on_an_assertion_without_the_change_proves_behaviour(trees):
    report = check(trees, ["test_new.py"])

    assert report["status"] == "pass", report["reason"]
    assert report["tests"]["test_new.py::test_add"]["verdict"] == "proves-behaviour"
    assert report["tests"]["test_new.py::test_add"]["at_head"] == "pass"
    assert report["tests"]["test_new.py::test_add"]["reverted"] == "behaviour"


def test_the_reverted_tree_has_base_source_and_head_tests(trees):
    report = check(trees, ["test_new.py"])

    reverted = revert.Path(report["reverted_tree"])
    assert (reverted / "app.py").read_text() == BASE_APP
    assert (reverted / "test_new.py").read_text() == TESTS["test_new.py"]


@pytest.mark.parametrize(
    ("test_id", "verdict"),
    [
        ("test_new.py::test_add", "proves-behaviour"),
        ("test_mul.py::test_mul", "missing-name"),
        ("test_ratio.py::test_ratio", "crash"),
        ("test_same.py::test_add_zero", "passes-without-change"),
        ("test_wrong.py::test_add_wrong", "head-fails"),
        ("test_unit.py::AddTest::test_add", "proves-behaviour"),
    ],
)
def test_each_kind_of_test_gets_its_verdict(trees, test_id, verdict):
    report = check(trees, list(TESTS))

    assert report["tests"][test_id]["verdict"] == verdict


def test_offending_tests_fail_the_check_and_are_named_in_the_reason(trees):
    report = check(trees, list(TESTS))

    assert report["status"] == "fail"
    for test_id in ("test_mul.py::test_mul", "test_ratio.py::test_ratio", "test_wrong.py::test_add_wrong"):
        assert test_id in report["reason"]
    assert "test_same.py" not in report["reason"]


def test_a_test_that_passes_without_the_change_alone_does_not_pass_the_check(trees):
    report = check(trees, ["test_same.py"])

    assert report["status"] == "fail"
    assert report["tests"]["test_same.py::test_add_zero"]["verdict"] == "passes-without-change"


def test_added_and_deleted_source_files_are_reverted(trees):
    head, base, work = trees
    (head / "added.py").write_text("X = 1\n")
    (base / "deleted.py").write_text("Y = 2\n")

    report = revert.run(
        head,
        base,
        [{"path": "added.py", "status": "A"}, {"path": "deleted.py", "status": "D"}],
        ["test_same.py"],
        work,
        sys.executable,
        ["-p", "no:cacheprovider"],
        [],
        "e2e_test_*.py",
        [],
    )

    reverted = revert.Path(report["reverted_tree"])
    assert not (reverted / "added.py").exists()
    assert (reverted / "deleted.py").read_text() == "Y = 2\n"


def test_a_timeout_fails_the_check_with_a_reason(trees):
    head, base, work = trees
    (head / "test_slow.py").write_text(
        textwrap.dedent("""\
            import time


            def test_slow():
                time.sleep(30)
                assert True
            """)
    )

    report = revert.run(
        head,
        base,
        [],
        ["test_slow.py"],
        work,
        sys.executable,
        ["-p", "no:cacheprovider"],
        [],
        "",
        [],
        timeout=2,
    )

    assert report["status"] == "fail"
    assert "timed out" in report["reason"]


# classify() on plugin-shaped records


def record(outcome="failed", exc_type="AssertionError", mro=None, message="", files=(), kind="test"):
    return {
        "nodeid": "t",
        "kind": kind,
        "outcome": outcome,
        "phase": "collect" if kind == "collect" else "call",
        "exc_type": exc_type,
        "exc_mro": mro if mro is not None else [exc_type, "Exception", "BaseException"],
        "message": message,
        "frames": [{"file": f, "line": 1, "function": "f"} for f in files],
    }


TEST_FILE = "bookmarks/tests/test_x.py"
SUPPORT = ["bookmarks/tests/helpers.py"]


@pytest.mark.parametrize(
    ("rec", "cause"),
    [
        (record(outcome="passed", exc_type=None, mro=[]), "pass"),
        (record(outcome="skipped", exc_type=None, mro=[]), "skip"),
        (record(files=["/r/bookmarks/tests/test_x.py"]), "behaviour"),
        (
            record(
                exc_type="playwright._impl._errors.AssertionErrorSubclass",
                mro=["playwright._impl._errors.AssertionErrorSubclass", "AssertionError", "Exception"],
                files=["/r/bookmarks/tests/test_x.py"],
            ),
            "behaviour",
        ),
        (
            record(
                files=[
                    "/r/bookmarks/tests/test_x.py",
                    "/venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py",
                ]
            ),
            "behaviour",
        ),
        (record(files=["/r/bookmarks/tests/helpers.py"]), "behaviour"),
        (record(files=["/r/bookmarks/models.py", "/r/bookmarks/views.py"]), "crash"),
        (record(exc_type="ImportError", message="cannot import name 'mul'"), "missing-name"),
        (
            record(exc_type="ModuleNotFoundError", mro=["ModuleNotFoundError", "ImportError", "Exception"]),
            "missing-name",
        ),
        (record(exc_type="NameError", message="name 'mul' is not defined"), "missing-name"),
        (
            record(exc_type="UnboundLocalError", mro=["UnboundLocalError", "NameError", "Exception"]),
            "crash",
        ),
        (record(exc_type="AttributeError", message="'Bookmark' object has no attribute 'x'"), "missing-name"),
        (record(exc_type="AttributeError", message="can't set attribute"), "crash"),
        (record(exc_type="TypeError", message="f() got an unexpected keyword argument 'x'"), "missing-name"),
        (
            record(exc_type="TypeError", message="f() missing 1 required positional argument: 'x'"),
            "missing-name",
        ),
        (record(exc_type="TypeError", message="unsupported operand type(s)"), "crash"),
        (
            record(
                exc_type="django.urls.exceptions.NoReverseMatch",
                mro=["django.urls.exceptions.NoReverseMatch", "Exception"],
            ),
            "missing-name",
        ),
        (record(exc_type="RuntimeError", kind="collect", outcome="error"), "missing-name"),
        (record(exc_type="ZeroDivisionError", files=["/r/bookmarks/tests/test_x.py"]), "crash"),
    ],
)
def test_classify(rec, cause):
    assert revert.classify(rec, TEST_FILE, SUPPORT) == cause


def test_a_file_whose_name_only_ends_like_the_test_file_does_not_count():
    rec = record(files=["/r/bookmarks/tests/old_test_x.py"])

    assert revert.classify(rec, "test_x.py", []) == "crash"


def test_the_test_helpers_go_back_to_the_base_version_too(trees):
    # The change added a name to app.py and the developers' helpers started using it, as linkding's
    # commit 573b6f5 did; with the head's helpers every test would fail on import, not on an assertion.
    head, base, work = trees
    (head / "app.py").write_text(HEAD_APP + "\nDEFAULT = 0\n")
    (head / "helpers.py").write_text(
        "from app import DEFAULT\n\n\ndef start(value=DEFAULT):\n    return value\n"
    )
    (base / "helpers.py").write_text("def start(value=0):\n    return value\n")
    (head / "test_helped.py").write_text(
        "from app import add\nfrom helpers import start\n\n\n"
        "def test_add():\n    assert add(start(), 2) == 2\n"
    )
    report = revert.run(
        head_tree=head,
        base_tree=base,
        changed_source=[{"path": "app.py", "status": "M"}],
        new_test_files=["test_helped.py"],
        workdir=work,
        python=sys.executable,
        pytest_args=["-p", "no:cacheprovider"],
        test_support=["helpers.py"],
        browser_glob="e2e_test_*.py",
        exclude_copy=[".git", "__pycache__"],
    )
    assert report["tests"]["test_helped.py::test_add"]["verdict"] == "proves-behaviour", report
    assert (work / "reverted" / "helpers.py").read_text() == (base / "helpers.py").read_text()
