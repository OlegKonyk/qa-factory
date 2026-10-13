import os
from pathlib import Path

import pytest

from factory.checks import mutants

BASE = """\
def same(a):
    return a


def edited(a):
    return a + 1


def commented(a):
    return a


def removed(a):
    return a


class K:
    def meth(self):
        return 1
"""

HEAD = """\
def same(a):
    return a


def edited(a):
    return a + 2


def commented(a):
    # now explained
    return a


def added(a):
    return a


class K:
    def meth(self):
        return 2
"""


def test_changed_functions():
    globs = mutants.changed_functions(BASE, HEAD, "pkg.mod")
    assert sorted(globs) == sorted(
        [
            "pkg.mod.x_edited__mutmut_*",
            "pkg.mod.x_added__mutmut_*",
            "pkg.mod.xǁKǁmeth__mutmut_*",
        ]
    )


def test_changed_functions_no_base_means_everything_is_new():
    assert mutants.changed_functions(None, "def f():\n    pass\n", "m") == ["m.x_f__mutmut_*"]


def test_changed_lines():
    assert mutants.changed_lines("a\nb\nc\n", "a\nB\nc\nd\n") == {2, 4}
    assert mutants.changed_lines("a\nb\n", "a\n") == set()


def test_function_def_line():
    assert mutants.function_def_line(HEAD, "edited") == 5
    assert mutants.function_def_line(HEAD, "K.meth") == 19
    assert mutants.function_def_line(HEAD, "missing") is None


MUTATED = """\
def x_f__mutmut_orig(a):
    return a + 1


def x_f__mutmut_1(a):
    return a - 1


def x_f__mutmut_2(a):
    return a + 1


def x_g__mutmut_orig(a):
    b = a
    return b + 1


def x_g__mutmut_1(a):
    b = a
    return b - 1


def x_g__mutmut_2(a):
    b = a
    c = b
    return b + 1
"""


def test_mutant_lines_first_body_line_is_offset_one():
    assert mutants.mutant_lines(MUTATED, "x_f") == {"x_f__mutmut_1": 1, "x_f__mutmut_2": None}


def test_mutant_lines_second_body_line_is_offset_two():
    result = mutants.mutant_lines(MUTATED, "x_g")
    assert result["x_g__mutmut_1"] == 2
    assert result["x_g__mutmut_2"] == 2  # a line was inserted; first non-equal position


def test_summarize_meta_counts_every_code_class():
    meta = {
        "exit_code_by_key": {
            "m.x_a__mutmut_1": 1,
            "m.x_a__mutmut_2": 3,
            "m.x_a__mutmut_3": 0,
            "m.x_a__mutmut_4": 5,
            "m.x_a__mutmut_5": 33,
            "m.x_a__mutmut_6": 36,
            "m.x_a__mutmut_7": -24,
            "m.x_a__mutmut_8": 99,
            "m.x_a__mutmut_9": None,
        }
    }
    counts = mutants.summarize_meta(meta)
    assert counts == {
        "generated": 9,
        "checked": 8,
        "killed": 2,
        "survived": 1,
        "no_tests": 2,
        "timeout": 2,
        "other": 1,
        "score": 2 / 3,
    }
    assert mutants.summarize_meta({"exit_code_by_key": {}})["score"] is None


LINKDING = Path("~/Library/Caches/qa-factory/linkding").expanduser()


@pytest.mark.linkding
@pytest.mark.skipif(not (LINKDING / "wt" / "head").exists(), reason="linkding clone is absent")
@pytest.mark.skipif(os.environ.get("QA_FACTORY_SLOW") != "1", reason="slow; set QA_FACTORY_SLOW=1")
def test_run_on_real_linkding(tmp_path):
    rel = "bookmarks/queries.py"
    base_src = (LINKDING / "wt" / "base" / rel).read_text()
    head_src = (LINKDING / "wt" / "head" / rel).read_text()
    globs = mutants.changed_functions(base_src, head_src, "bookmarks.queries")
    result = mutants.run(
        head_tree=LINKDING / "wt" / "head",
        python=LINKDING / "repo" / ".venv" / "bin" / "python",
        source_package="bookmarks",
        only_mutate=[rel],
        test_files=["bookmarks/tests/test_queries.py"],
        globs=globs,
        workdir=tmp_path,
        pytest_add_cli_args=["-p", "no:cacheprovider", "-o", "django_find_project=false"],
        pre_create_dirs=["data/assets", "data/favicons", "data/previews"],
        exclude_copy=[".git", "node_modules", ".venv", "mutants", "__pycache__", ".pytest_cache"],
        changed_lines_by_file={rel: mutants.changed_lines(base_src, head_src)},
    )
    assert result["status"] == "pass", result["stdout_tail"]
    assert result["checked"] > 0
    assert result["killed"] > 0


def test_mutant_lines_finds_method_mutants_inside_the_class():
    src = (
        "class C:\n"
        "    def xǁCǁm__mutmut_orig(self, a):\n"
        "        return a + 1\n"
        "    def xǁCǁm__mutmut_1(self, a):\n"
        "        return a - 1\n"
    )
    assert mutants.mutant_lines(src, "xǁCǁm") == {"xǁCǁm__mutmut_1": 1}


def test_classify_exit_reports_no_mutants_when_mutmut_matched_nothing():
    out = "...\nAssertionError: " + mutants.NOTHING_MATCHES + "\n\nFilter: ('m.x_f__mutmut_*',)"
    assert mutants.classify_exit(False, 1, True, out, 10) == (
        "pass",
        "mutmut made no mutant for any changed function (it skips some shapes)",
        True,
    )
    assert mutants.classify_exit(False, 1, False, "boom", 10) == (
        "fail",
        "mutmut exited with code 1 and wrote no results",
        False,
    )
    assert mutants.classify_exit(True, None, False, "", 10)[0] == "fail"
    assert mutants.classify_exit(False, 0, True, "done", 10) == ("pass", "mutmut ran", False)
