"""The run summary: numbers read from a hand-built run folder and from the first real run."""

import io
import json
from pathlib import Path

import pytest

from factory import __main__ as cli
from factory import summary

REAL = Path(__file__).resolve().parent.parent / "docs/runs/2026-10-08-linkding-sort-by-modified/records"


def _w(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _test(verdict, at_head="pass"):
    return {"at_head": at_head, "reverted": "x", "verdict": verdict, "message": ""}


def _mutation(killed=3, checked=4):
    run = {
        "checked": checked,
        "killed": killed,
        "score": killed / checked,
        "on_changed_lines": {"checked": 2, "killed": 2, "score": 1.0},
    }
    return {"status": "pass", "result": {"runs": {"generated": run}}}


def _step(run, index, name, cost, duration, model=None):
    metrics = {"cost_usd": cost, **({"model": model} if model else {})}
    _w(
        run / "steps" / f"0{index}-{name}.json",
        {
            "step": name,
            "index": index,
            "status": "pass",
            "duration_s": duration,
            "output": {"status": "pass", "metrics": metrics},
        },
    )


def make_run(root: Path, ticket_id="t-1", two_rounds=True) -> Path:
    run = root / ticket_id
    _w(run / "ticket.json", {"id": ticket_id, "qa_mode": "blind"})
    _step(run, 1, "frame", 0.5, 10.0, "sonnet")
    _step(run, 4, "verify", 2.0, 100.0)
    _w(run / "steps" / "04-verify.round1.json", {"step": "verify", "index": 4, "status": "fail"})
    verify = run / "verify"
    a, b, c = "t/test_a.py::A::t1", "t/e2e_test_b.py::B::t2", "t/test_a.py::A::t3"
    if two_rounds:
        _w(
            verify / "report.json",
            {
                "rounds": [
                    {"round": 1, "kind": "write", "failure": {"check": "revert", "reason": "weak"}},
                    {"round": 2, "kind": "repair", "failure": None},
                ],
                "blind_audit": {"leaks": 0},
            },
        )
        tests1 = {a: _test("proves-behaviour"), b: _test("head-fails", "fail"), c: _test("crash")}
        _w(verify / "rounds/1/revert.json", {"status": "pass", "result": {"tests": tests1}})
        tests2 = {a: _test("proves-behaviour"), b: _test("proves-behaviour"), c: _test("proves-behaviour")}
        _w(verify / "rounds/2/revert.json", {"status": "pass", "result": {"tests": tests2}})
        _w(verify / "rounds/2/mutation.json", _mutation())
        _w(verify / "escalation-1.json", {"decision": "retry"})
        _w(
            run / "rounds.json",
            {
                "caps": {"usd": 15},
                "spent_usd": 3.0,
                "entries": [{"kind": "write"}, {"kind": "repair"}, {"kind": "advice"}],
            },
        )
    else:
        _w(verify / "report.json", {"checks": {}, "metrics": {}})
        _w(verify / "revert.json", {"status": "pass", "result": {"tests": {a: _test("proves-behaviour")}}})
        _w(verify / "mutation.json", _mutation(1, 2))
    return run


def test_two_rounds(tmp_path):
    s = summary.summarize(make_run(tmp_path))
    assert s["ticket"] == "t-1" and s["qa_mode"] == "blind"
    first, final = s["first_round"], s["final_round"]
    assert (first["round"], final["round"]) == (1, 2)
    assert (first["tests"], first["tests_api"], first["tests_browser"]) == (3, 2, 1)
    assert (first["pass_at_head"], first["fail_at_base_on_assertion"]) == (2, 1)
    assert (first["head_fails"], first["crash"], first["pass_on_both"], first["missing_name"]) == (1, 1, 0, 0)
    assert first["mutation"] == {}
    assert final["fail_at_base_on_assertion"] == 3 and final["crash"] == 0
    assert final["mutation"]["generated"] == {
        "checked": 4,
        "killed": 3,
        "score": 0.75,
        "changed_lines": {"checked": 2, "killed": 2, "score": 1.0},
    }
    assert [r["failure"] for r in s["rounds"]] == ["revert: weak", None]
    assert s["decisions"] == ["retry"]
    assert s["stages"]["frame"]["model"] == "sonnet"
    assert s["stages"]["verify"]["earlier_runs"] == 1
    assert "plan" not in s["stages"]
    assert s["spend_usd"] == 2.5
    assert s["ledger"]["writer_rounds_used"] == 1 and s["ledger"]["advice_used"] == 1
    assert s["blind_audit"] == {"leaks": 0}


def test_run_without_rounds_uses_top_level(tmp_path):
    s = summary.summarize(make_run(tmp_path, two_rounds=False))
    assert s["first_round"] is s["final_round"]
    assert s["final_round"]["tests"] == 1
    assert s["final_round"]["mutation"]["generated"]["killed"] == 1
    assert s["ledger"] is None and s["decisions"] == []


def test_table_has_a_column_per_run(tmp_path):
    runs = [make_run(tmp_path, "t-1"), make_run(tmp_path, "t-2", two_rounds=False)]
    out = summary.render([summary.summarize(r) for r in runs])
    header = out.splitlines()[0]
    assert header == "| number | t-1 | t-2 |"
    row = next(line for line in out.splitlines() if line.startswith("| final_round tests |"))
    assert row == "| final_round tests | 3 | 1 |"
    assert "| first_round mutation generated killed | - | 1 |" in out


def test_cli_writes_json_for_one_run(tmp_path, capsys):
    run = make_run(tmp_path)
    assert cli.main(["summary", str(run)]) == 0
    assert "| number | t-1 |" in capsys.readouterr().out
    assert json.loads((run / "summary.json").read_text())["ticket"] == "t-1"


def test_cli_several_runs_write_json_only_when_asked(tmp_path):
    a, b = make_run(tmp_path, "t-1"), make_run(tmp_path, "t-2")
    cli.main(["summary", str(a), str(b)])
    assert not (a / "summary.json").exists()
    target = tmp_path / "both.json"
    cli.main(["summary", str(a), str(b), "--json", str(target)])
    assert [d["ticket"] for d in json.loads(target.read_text())] == ["t-1", "t-2"]


@pytest.mark.skipif(not REAL.exists(), reason="first run's records not in the checkout")
def test_first_real_run():
    final = summary.summarize(REAL)["final_round"]
    assert (final["tests"], final["fail_at_base_on_assertion"], final["pass_on_both"]) == (6, 5, 1)
    generated = final["mutation"]["generated"]
    assert (generated["killed"], generated["checked"]) == (27, 108)
    assert (generated["changed_lines"]["killed"], generated["changed_lines"]["checked"]) == (10, 10)


def test_a_path_that_is_not_a_run_folder_is_refused(tmp_path):
    buf = io.StringIO()
    assert summary.main([str(tmp_path / "nope")], out=buf) == 2
    assert "not a run folder" in buf.getvalue()
    assert not (tmp_path / "nope").exists()
