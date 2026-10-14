"""`python -m factory mutation <run folder>` (factory/checks/mutation_rerun.py), with a fake mutmut."""

import io
import json
from pathlib import Path

import pytest

from factory.__main__ import main as cli
from factory.checks import mutation_rerun
from factory.steps import verify

TEST_FILE = "tests/test_gen.py"


def _run_folder(tmp_path):
    head, base = tmp_path / "head", tmp_path / "base"
    for tree, body in ((head, "def f(x):\n    return x + 1\n"), (base, "def f(x):\n    return x\n")):
        (tree / "pkg").mkdir(parents=True)
        (tree / "pkg" / "mod.py").write_text(body)
    run = tmp_path / "run"
    (run / "steps").mkdir(parents=True)
    (run / "implement").mkdir()
    (run / "implement" / "changed_source.json").write_text(
        json.dumps([{"path": "pkg/mod.py", "status": "M"}])
    )
    (run / "implement" / "changed_tests.json").write_text("[]")
    (run / "verify" / "tests" / "tests").mkdir(parents=True)
    (run / "verify" / "tests" / TEST_FILE).write_text("def test_f(): pass\n")
    (run / "verify" / "tests_manifest.json").write_text(json.dumps({"files": [TEST_FILE]}))
    (run / "verify" / "mutation.json").write_text('{"status": "pass", "result": "verify\'s own"}')
    app = {
        "name": "demo",
        "python": "py",
        "source_package": "pkg",
        "api_tests_dir": "tests",
        "exclude_copy": [],
        "mutmut": {"pytest_add_cli_args": [], "pre_create_dirs": []},
    }
    record = {
        "input": {
            "repo": {"head_tree": str(head), "base_tree": str(base), "app": app},
            "ticket": {"id": "demo-x", "title": "x"},
        },
        "output": {
            "artifacts": {
                "changed_source": str(run / "implement" / "changed_source.json"),
                "changed_tests": str(run / "implement" / "changed_tests.json"),
            }
        },
    }
    (run / "steps" / "03-implement.json").write_text(json.dumps(record))
    return run, head


def _fake(result, seen):
    def fake_run(tree, python, pkg, only, files, globs, workdir, *rest):
        seen.append(
            {
                "files": files,
                "globs": globs,
                "workdir": workdir,
                "test_present": Path(tree, TEST_FILE).is_file(),
            }
        )
        return dict(result)

    return fake_run


RAN = {
    "status": "pass",
    "reason": "mutmut ran",
    "no_mutants": False,
    "generated": 4,
    "checked": 4,
    "killed": 3,
    "survived": 1,
    "score": 0.75,
    "on_changed_lines": {"checked": 2, "killed": 2, "survived": 0, "score": 1.0},
    "unmutated": ["pkg.mod.x_g__mutmut_*"],
}


def test_reruns_the_check_from_the_record_and_writes_beside_verifys_file(tmp_path, monkeypatch):
    run, head = _run_folder(tmp_path)
    seen = []
    monkeypatch.setattr(verify.mutants, "run", _fake(RAN, seen))
    out = io.StringIO()
    assert mutation_rerun.main(str(run), out) == 0
    assert seen[0]["test_present"] and (head / TEST_FILE).is_file()  # put back from verify/tests/
    assert seen[0]["files"] == [TEST_FILE] and seen[0]["globs"] == ["pkg.mod.x_f__mutmut_*"]
    assert seen[0]["workdir"] == str(run / "verify" / "mutation-rerun" / "mutation" / "generated")
    lines = out.getvalue().splitlines()
    assert lines[0] == (
        "generated: checked 4, killed 3, survived 1, score 0.75; "
        "on the changed lines: checked 2, killed 2, survived 0, score 1.00"
    )
    assert lines[1].startswith("generated_and_developers: checked 4")  # no developers' test: two sets
    assert lines[2:] == ["skipped: mutmut made no mutant for pkg.mod.x_g__mutmut_*"]
    saved = json.loads((run / "verify" / "mutation-rerun.json").read_text())
    assert saved["status"] == "pass" and saved["restored_tests"] == [TEST_FILE]
    assert saved["result"]["runs"]["generated"]["killed"] == 3
    assert json.loads((run / "verify" / "mutation.json").read_text())["result"] == "verify's own"


def test_no_mutant_at_all_is_skipped_with_exit_zero(tmp_path, monkeypatch):
    run, _ = _run_folder(tmp_path)
    reason = "mutmut made no mutant for any changed function (it skips some shapes)"
    monkeypatch.setattr(
        verify.mutants, "run", _fake({"status": "pass", "reason": reason, "no_mutants": True}, [])
    )
    out = io.StringIO()
    assert mutation_rerun.main(str(run), out) == 0
    assert out.getvalue().splitlines()[-1] == f"skipped: {reason}: pkg.mod.x_f__mutmut_*"


def test_tests_that_kill_nothing_on_the_changed_lines_still_exit_zero(tmp_path, monkeypatch):
    run, _ = _run_folder(tmp_path)
    weak = {**RAN, "killed": 0, "survived": 4, "score": 0.0, "unmutated": []}
    weak["on_changed_lines"] = {"checked": 2, "killed": 0, "survived": 2, "score": 0.0}
    monkeypatch.setattr(verify.mutants, "run", _fake(weak, []))
    out = io.StringIO()
    assert mutation_rerun.main(str(run), out) == 0
    assert out.getvalue().splitlines()[-1].startswith("fail: the generated tests kill no mutant")


@pytest.mark.parametrize(
    "result",
    [
        {"status": "fail", "reason": "mutmut exited with code 2 and wrote no results", "no_mutants": False},
        RuntimeError("boom"),
    ],
)
def test_mutmut_not_running_is_exit_one(tmp_path, monkeypatch, result):
    run, _ = _run_folder(tmp_path)

    def fake_run(*a, **k):
        if isinstance(result, Exception):
            raise result
        return dict(result)

    monkeypatch.setattr(verify.mutants, "run", fake_run)
    out = io.StringIO()
    assert mutation_rerun.main(str(run), out) == 1
    assert "mutmut did not run" in out.getvalue() or "error: RuntimeError: boom" in out.getvalue()


def test_a_folder_without_an_implement_record_is_exit_one(tmp_path):
    assert mutation_rerun.main(str(tmp_path / "nowhere"), io.StringIO()) == 1


def test_the_cli_has_the_subcommand(tmp_path, monkeypatch, capsys):
    run, _ = _run_folder(tmp_path)
    monkeypatch.setattr(verify.mutants, "run", _fake(RAN, []))
    assert cli(["mutation", str(run)]) == 0
    assert capsys.readouterr().out.startswith("generated: checked 4")
