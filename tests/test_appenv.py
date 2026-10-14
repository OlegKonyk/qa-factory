import os
import stat
import sys

import pytest

from factory.checks import suite
from factory.checks.appenv import PROXY_VARS, app_env


@pytest.fixture
def no_proxy_vars(monkeypatch):
    for name in PROXY_VARS:
        monkeypatch.delenv(name, raising=False)


def test_path_starts_with_the_interpreter_folder_and_keeps_the_old_path(monkeypatch):
    monkeypatch.setenv("PATH", os.pathsep.join(["/usr/bin", "/bin"]))
    env = app_env("/venv/bin/python")
    assert env["PATH"].split(os.pathsep) == ["/venv/bin", "/usr/bin", "/bin"]


def test_path_already_starting_with_the_folder_is_not_doubled(monkeypatch):
    monkeypatch.setenv("PATH", os.pathsep.join(["/venv/bin", "/usr/bin"]))
    env = app_env("/venv/bin/python")
    assert env["PATH"].split(os.pathsep) == ["/venv/bin", "/usr/bin"]


def test_tilde_in_the_interpreter_path_is_expanded(monkeypatch):
    monkeypatch.setenv("HOME", "/home/someone")
    monkeypatch.setenv("PATH", "/usr/bin")
    assert app_env("~/venv/bin/python")["PATH"].split(os.pathsep)[0] == "/home/someone/venv/bin"


def test_extra_wins_over_the_inherited_environment(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/old")
    env = app_env("/venv/bin/python", PYTHONPATH="/new", QA_FACTORY_FAILSORT_OUT="/out.jsonl")
    assert env["PYTHONPATH"] == "/new"
    assert env["QA_FACTORY_FAILSORT_OUT"] == "/out.jsonl"


def test_mutmut_sets_no_proxy_when_no_proxy_variable_is_set(no_proxy_vars):
    assert app_env("/venv/bin/python", mutmut=True)["no_proxy"] == "*"


def test_without_mutmut_no_proxy_is_not_added(no_proxy_vars):
    assert "no_proxy" not in app_env("/venv/bin/python")


@pytest.mark.parametrize(("name", "value"), [("HTTP_PROXY", "http://proxy:3128"), ("no_proxy", "localhost")])
def test_mutmut_leaves_a_set_proxy_variable_alone(no_proxy_vars, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    env = app_env("/venv/bin/python", mutmut=True)
    assert env[name] == value
    assert env.get("no_proxy") == (value if name == "no_proxy" else None)


def _executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def test_the_suite_check_puts_the_interpreter_folder_on_the_tests_path(tmp_path):
    # A symlink to the venv's interpreter outside the venv starts the base Python without pytest,
    # so the fake environment's `python` is a wrapper that runs this one.
    bin_dir = tmp_path / "env" / "bin"
    bin_dir.mkdir(parents=True)
    _executable(bin_dir / "python", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    _executable(bin_dir / "probe", "#!/bin/sh\nexit 0\n")
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "test_probe.py").write_text(
        'import shutil\n\n\ndef test_probe_is_on_path():\n    assert shutil.which("probe") is not None\n'
    )
    result = suite.run(tree, bin_dir / "python", [["test_probe.py"]], ["-p", "no:cacheprovider"])
    assert result["status"] == "pass", result["runs"][0]["tail"]
    assert "1 passed" in result["runs"][0]["summary"]
