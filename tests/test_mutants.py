import json
import os
import subprocess
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


def _unchanged_lines_keep_their_place(src: str, out: str, commented: set[int], assignments: int = 1) -> None:
    """Same line count up to the original end (then a blank line, a note, the assignments); every
    line not a decorator line is unchanged at its number; every decorator line is a comment."""
    before, after = src.splitlines(), out.splitlines()
    assert len(after) == len(before) + 2 + assignments
    for n, line in enumerate(before, 1):
        if n in commented:
            assert after[n - 1].lstrip().startswith("#"), (n, after[n - 1])
        else:
            assert after[n - 1] == line, (n, after[n - 1])


def test_undecorate_top_level_function():
    src = "import x\n\n\n@dec\ndef f(a):\n    return a\n\n\ny = 1\n"
    out = mutants.undecorate(src)
    _unchanged_lines_keep_their_place(src, out, {4})
    assert out.splitlines()[3] == "# @dec"
    assert out.splitlines()[-1] == "f = dec(f)"


def test_undecorate_method():
    src = 'class C:\n    x = 1\n\n    @requires(str, "uri")\n    def m(self):\n        return 1\n'
    out = mutants.undecorate(src)
    _unchanged_lines_keep_their_place(src, out, {4})
    assert out.splitlines()[3] == '    # @requires(str, "uri")'
    assert out.splitlines()[-1] == "C.m = requires(str, 'uri')(C.m)"


def test_undecorate_two_decorators_apply_bottom_up():
    src = "@a\n@b\ndef f():\n    pass\n"
    out = mutants.undecorate(src)
    _unchanged_lines_keep_their_place(src, out, {1, 2})
    assert out.splitlines()[-1] == "f = a(b(f))"


def test_undecorate_multi_line_decorator():
    src = "@route(\n    '/x',\n    methods=['GET'],\n)\ndef f():\n    return 1\n"
    out = mutants.undecorate(src)
    _unchanged_lines_keep_their_place(src, out, {1, 2, 3, 4})
    assert out.splitlines()[:4] == ["# @route(", "    #", "    #", "#"]
    assert out.splitlines()[4] == "def f():"
    assert out.splitlines()[-1] == "f = route('/x', methods=['GET'])(f)"


def test_undecorate_leaves_staticmethod_property_and_nested_functions():
    src = (
        "class C:\n"
        "    @staticmethod\n"
        "    def s():\n"
        "        return 1\n"
        "\n"
        "    @classmethod\n"
        "    @cache\n"
        "    def k(cls):\n"
        "        return 1\n"
        "\n"
        "    @property\n"
        "    def p(self):\n"
        "        return 1\n"
        "\n"
        "\n"
        "def outer(func):\n"
        "    @wraps(func)\n"
        "    def inner():\n"
        "        return func()\n"
        "    return inner\n"
    )
    out = mutants.undecorate(src)
    assert out == src and len(out.splitlines()) == len(src.splitlines())


def test_undecorate_leaves_a_name_defined_twice():
    src = "@overload\ndef f(a: int): ...\n@overload\ndef f(a: str): ...\ndef f(a):\n    return a\n"
    out = mutants.undecorate(src)
    assert out == src and len(out.splitlines()) == len(src.splitlines())


def test_undecorate_runs_the_same_as_the_decorated_module():
    src = (
        "def twice(f):\n"
        "    return lambda *a: f(*a) * 2\n"
        "\n"
        "\n"
        "def plus(n):\n"
        "    return lambda f: lambda *a: f(*a) + n\n"
        "\n"
        "\n"
        "@twice\n"
        "@plus(1)\n"
        "def g(x):\n"
        "    return x\n"
        "\n"
        "\n"
        "class C:\n"
        "    @plus(10)\n"
        "    def m(self, x):\n"
        "        return x\n"
    )
    plain, rewritten = {}, {}
    exec(src, plain)
    out = mutants.undecorate(src)
    _unchanged_lines_keep_their_place(src, out, {9, 10, 16}, assignments=2)
    exec(out, rewritten)
    assert plain["g"](3) == rewritten["g"](3) == 8
    assert plain["C"]().m(1) == rewritten["C"]().m(1) == 11


def test_changed_functions_in_a_package_init_use_the_package_name():
    assert mutants.changed_functions(None, "def f():\n    pass\n", "pkg.utils.__init__") == [
        "pkg.utils.x_f__mutmut_*"
    ]


def test_run_mutates_an_undecorated_copy_and_names_globs_without_a_mutant(tmp_path, monkeypatch):
    head = tmp_path / "head"
    (head / "pkg").mkdir(parents=True)
    src = "@dec\ndef f(a):\n    return a\n\n\ndef dec(f):\n    return f\n"
    (head / "pkg" / "mod.py").write_text(src)
    seen = {}

    def fake_mutmut(cmd, cwd, **kwargs):
        seen["copy"] = (Path(cwd) / "pkg" / "mod.py").read_text()
        (Path(cwd) / "mutants" / "pkg").mkdir(parents=True)
        (Path(cwd) / "mutants" / "pkg" / "mod.py").write_text("")
        meta = {"exit_code_by_key": {"pkg.mod.x_f__mutmut_1": 1}}
        (Path(cwd) / "mutants" / "pkg" / "mod.py.meta").write_text(json.dumps(meta))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(mutants.subprocess, "run", fake_mutmut)
    globs = ["pkg.mod.x_f__mutmut_*", "pkg.mod.x_dec__mutmut_*"]
    result = mutants.run(head, "py", "pkg", ["pkg/mod.py"], [], globs, tmp_path / "w", [], [], [], {})
    assert seen["copy"] == mutants.undecorate(src) != src
    assert (head / "pkg" / "mod.py").read_text() == src  # the worktree keeps its decorators
    assert result["killed"] == 1 and result["unmutated"] == ["pkg.mod.x_dec__mutmut_*"]


def test_undecorate_leaves_a_method_whose_decorator_names_a_class_attribute():
    src = (
        "class Store:\n"
        "    _lock = Lock()\n"
        "\n"
        "    @synchronized(_lock)\n"
        "    def put(self, k):\n"
        "        return k\n"
        "\n"
        "    @requires(str)\n"
        "    def get(self, k):\n"
        "        return k\n"
    )
    out, kept = mutants.undecorate_with_reasons(src)
    assert out.splitlines()[3] == "    @synchronized(_lock)"
    assert out.splitlines()[-1] == "Store.get = requires(str)(Store.get)"
    assert kept == [("Store.put", "its decorator names _lock from the class body")]


def test_undecorate_leaves_abstractmethod_and_lists_why():
    src = "class A(ABC):\n    @abc.abstractmethod\n    def f(self):\n        return 1\n"
    out, kept = mutants.undecorate_with_reasons(src)
    assert out == src == mutants.undecorate(src)
    assert kept == [("A.f", "@abstractmethod is read while the class is created")]


def test_undecorate_does_not_list_a_lone_staticmethod():
    src = "class C:\n    @staticmethod\n    def s():\n        return 1\n"
    assert mutants.undecorate_with_reasons(src) == (src, [])


REWRITE_NOTE = "# Decorators moved here by qa-factory"


def _write_meta(cwd: Path, codes: dict) -> None:
    (cwd / "mutants" / "pkg").mkdir(parents=True, exist_ok=True)
    (cwd / "mutants" / "pkg" / "mod.py").write_text("")
    (cwd / "mutants" / "pkg" / "mod.py.meta").write_text(json.dumps({"exit_code_by_key": codes}))


def _decorated_head(tmp_path: Path) -> Path:
    head = tmp_path / "head"
    (head / "pkg").mkdir(parents=True)
    src = (
        "class C:\n"
        "    _lock = 1\n"
        "\n"
        "    @synchronized(_lock)\n"
        "    def put(self):\n"
        "        return 1\n"
        "\n"
        "\n"
        "@dec\n"
        "def f(a):\n"
        "    return a\n"
    )
    (head / "pkg" / "mod.py").write_text(src)
    return head


GLOBS = ["pkg.mod.x_f__mutmut_*", "pkg.mod.xǁCǁput__mutmut_*"]


def test_run_falls_back_to_the_plain_copy_when_the_rewrite_breaks_the_import(tmp_path, monkeypatch):
    head = _decorated_head(tmp_path)
    copies = []

    def fake_mutmut(cmd, cwd, **kwargs):
        cwd = Path(cwd)
        copies.append((cwd / "pkg" / "mod.py").read_text())
        if REWRITE_NOTE in copies[-1]:  # as measured: .meta written, every code null, exit 1
            _write_meta(cwd, {"pkg.mod.x_f__mutmut_1": None})
            return subprocess.CompletedProcess(
                cmd, 1, "NameError\nfailed to collect stats. runner returned 2\n", ""
            )
        _write_meta(cwd, {"pkg.mod.x_g__mutmut_1": 1})
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(mutants.subprocess, "run", fake_mutmut)
    result = mutants.run(head, "py", "pkg", ["pkg/mod.py"], [], GLOBS, tmp_path / "w", [], [], [], {})
    assert len(copies) == 2 and REWRITE_NOTE in copies[0]
    assert copies[1] == (head / "pkg" / "mod.py").read_text()
    assert result["undecorate"] == (
        "fallen back: mutmut exited with code 1 and checked no mutant "
        "(failed to collect stats. runner returned 2)"
    )
    assert result["status"] == "pass" and result["killed"] == 1 and result["left_decorated"] == []


def test_run_lists_what_it_left_decorated_and_does_not_fall_back_after_checking_a_mutant(
    tmp_path, monkeypatch
):
    head = _decorated_head(tmp_path)
    copies = []

    def fake_mutmut(cmd, cwd, **kwargs):
        copies.append((Path(cwd) / "pkg" / "mod.py").read_text())
        _write_meta(Path(cwd), {"pkg.mod.x_f__mutmut_1": 0, "pkg.mod.x_f__mutmut_2": None})
        return subprocess.CompletedProcess(cmd, 1, "a worker crashed\n", "")

    monkeypatch.setattr(mutants.subprocess, "run", fake_mutmut)
    result = mutants.run(head, "py", "pkg", ["pkg/mod.py"], [], GLOBS, tmp_path / "w", [], [], [], {})
    assert len(copies) == 1 and REWRITE_NOTE in copies[0]
    assert "undecorate" not in result and result["checked"] == 1
    assert result["left_decorated"] == [
        {"file": "pkg/mod.py", "function": "C.put", "reason": "its decorator names _lock from the class body"}
    ]
