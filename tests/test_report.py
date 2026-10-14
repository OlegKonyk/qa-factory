"""The run report: one Markdown page per run, from hand-built run folders and the three committed runs."""

import io
import json
import re
import shutil
from pathlib import Path

import pytest

from factory import __main__ as cli
from factory import report, summary

RUNS = Path(__file__).resolve().parent.parent / "docs/runs"
SORT = "2026-10-08-linkding-sort-by-modified"
SORT_BLIND = "2026-10-10-linkding-sort-by-modified-blind"
BUNDLES = "2026-10-10-linkding-bundle-filters-blind"


def _w(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _copy_run(tmp_path: Path, name: str) -> Path:
    """The committed records (and their sibling testcases/) copied so nothing is written into docs/."""
    source = RUNS / name
    if not (source / "records").exists():
        pytest.skip(f"{name} records not in the checkout")
    shutil.copytree(source / "records", tmp_path / name / "records")
    if (source / "testcases").is_dir():
        shutil.copytree(source / "testcases", tmp_path / name / "testcases")
    return tmp_path / name / "records"


def _section(page: str, heading: str) -> str:
    """The text under a heading, up to the next heading of the same or a higher level."""
    level = heading.split(" ")[0]
    start = page.index(heading + "\n") + len(heading) + 1
    stop = re.search(rf"^#{{1,{len(level)}}} ", page[start:], re.MULTILINE)
    return page[start : start + stop.start()] if stop else page[start:]


def _rows(text: str) -> list[str]:
    """Table body rows: lines starting with "| " minus each table's header row."""
    lines = text.splitlines()
    return [
        line
        for i, line in enumerate(lines)
        if line.startswith("| ") and not (i + 1 < len(lines) and lines[i + 1].startswith("|---"))
    ]


def _final_round_files(records: Path) -> tuple[dict, dict]:
    """The final round's revert tests and mutation runs, read straight from the files."""
    verify = records / "verify"
    rounds = json.loads((verify / "report.json").read_text()).get("rounds")
    folder = verify / "rounds" / str(rounds[-1]["round"]) if rounds else verify
    tests = json.loads((folder / "revert.json").read_text())["result"]["tests"]
    runs = json.loads((folder / "mutation.json").read_text())["result"]["runs"]
    return tests, runs


@pytest.mark.parametrize("name", [SORT, SORT_BLIND, BUNDLES])
def test_committed_runs(tmp_path, name):
    records = _copy_run(tmp_path, name)
    assert cli.main(["report", str(records)]) == 0
    page = (records / "report.md").read_text()
    s = summary.summarize(records)
    tests, runs = _final_round_files(records)

    test_rows = _rows(_section(page, "## Tests"))
    for node in tests:
        file, _, test = node.partition("::")
        assert any(f"| {file} | {test} |" in row for row in test_rows), node
    for key in summary.NUMBER_KEYS:
        assert f"| {key} | {s['final_round'][key]} |" in page

    mutation = _section(page, "## Mutation")
    for set_name, run in runs.items():
        survived = [m for m in run["mutants"].values() if m["status"] == "survived"]
        listed = _rows(_section(mutation, f"#### {set_name}: {len(survived)} survived"))
        left_out = re.search(
            r"(\d+) more surviving mutants", _section(mutation, f"#### {set_name}: {len(survived)} survived")
        )
        assert len(listed) + (int(left_out.group(1)) if left_out else 0) == len(survived)
        numbers = s["final_round"]["mutation"][set_name]
        assert f"| {set_name} | {numbers['checked']} | {numbers['killed']} |" in mutation


def test_sort_run_lists_its_six_cases_with_links(tmp_path):
    records = _copy_run(tmp_path, SORT)
    page = report.render(records)
    titles = [
        p.read_text().splitlines()[0].lstrip("# ")
        for p in sorted((records.parent / "testcases").glob("*.md"))
    ]
    assert len(titles) == 6
    for title in titles:
        assert title in page
    assert "[TC-bookmarks-001.md](../testcases/TC-bookmarks-001.md)" in page
    assert "not in this folder" not in page
    assert "/Users/" not in page


def test_sort_run_mutants_beyond_thirty_are_counted_not_listed(tmp_path):
    records = _copy_run(tmp_path, SORT)
    page = report.render(records)
    assert "#### generated: 81 survived" in page
    assert "51 more surviving mutants not on changed lines were left out." in page


def test_bundles_run_says_no_cases_and_why(tmp_path):
    page = report.render(_copy_run(tmp_path, BUNDLES))
    assert "No readable cases were written. Verify ended with: spend cap reached" in page
    assert "verify fail: spend cap reached" in page
    assert "review not run; ship not run" in page
    assert "Stronger model's decisions: cannot_decide" in page
    assert "| writer rounds used | 1 |" in page
    assert "Total spend: 8.4729 USD (measured, from the run's records)." in page


def _mutants(survived_changed: int, survived_other: int, killed: int = 2) -> dict:
    mutants = {}
    for i in range(survived_changed):
        mutants[f"m.changed_{i}"] = {"status": "survived", "line": 10, "changed_line": True}
    for i in range(survived_other):
        mutants[f"m.other_{i}"] = {"status": "survived", "line": 100 + i, "changed_line": False}
    for i in range(killed):
        mutants[f"m.killed_{i}"] = {"status": "killed", "line": 5, "changed_line": True}
    return mutants


def make_run(root: Path, with_mutation=True) -> Path:
    """A run whose Verify stopped at a question, with one case file that is not in the folder."""
    run = root / "t-1"
    _w(run / "ticket.json", {"id": "t-1", "title": "A ticket", "qa_mode": "blind"})
    _w(
        run / "steps/01-frame.json",
        {"step": "frame", "status": "pass", "duration_s": 3.0, "output": {"metrics": {"cost_usd": 0.5}}},
    )
    _w(
        run / "steps/02-plan.json",
        {"step": "plan", "status": "fail", "duration_s": 1.0, "output": {"reason": "no plan"}},
    )
    _w(
        run / "steps/04-verify.json",
        {
            "step": "verify",
            "status": "needs_person",
            "duration_s": 9.0,
            "output": {"gate": {"who": "Oleg", "question": "Approve these tests?", "context": {}}},
        },
    )
    verify = run / "verify"
    tests = {
        "t/test_a.py::A::test_one": {
            "at_head": "pass",
            "reverted": "behaviour",
            "verdict": "proves-behaviour",
            "message": "first line " + "x" * 200 + "\nsecond line",
        },
        "t/e2e_test_b.py::B::test_two": {
            "at_head": "pass",
            "reverted": "pass",
            "verdict": "passes-without-change",
        },
    }
    _w(verify / "report.json", {"checks": {}})
    _w(verify / "revert.json", {"status": "pass", "result": {"tests": tests}})
    if with_mutation:
        run_doc = {
            "checked": 37,
            "killed": 2,
            "score": 2 / 37,
            "on_changed_lines": {"checked": 5, "killed": 2, "score": 0.4},
            "mutants": _mutants(3, 32),
        }
        _w(verify / "mutation.json", {"status": "pass", "result": {"runs": {"generated": run_doc}}})
    _w(
        verify / "test_cases.json",
        {"status": "pass", "result": {"files": ["area/TC-gone.md", "area/TC-here.md"]}},
    )
    (verify / "testcases/area").mkdir(parents=True)
    (verify / "testcases/area/TC-here.md").write_text("intro\n# TC-here: the title\n")
    return run


def test_hand_built_run(tmp_path):
    run = make_run(tmp_path)
    page = report.render(run)
    assert page.startswith("# t-1: A ticket\n")
    assert (
        "Steps: frame pass; plan fail: no plan; implement not run; "
        "verify needs_person: Approve these tests?; review not run; ship not run." in page
    )
    assert "| t/test_a.py | A::test_one | API | pass | fails on the old code: proves the change |" in page
    assert f"| first line {'x' * 89} |" in page and "second line" not in page
    assert (
        "| t/e2e_test_b.py | B::test_two | browser | pass | passes on the old code too: proves nothing | - |"
        in page
    )
    assert "| area/TC-gone.md | - | not in this folder |" in page
    assert "| area/TC-here.md | TC-here: the title | [TC-here.md](verify/testcases/area/TC-here.md) |" in page
    assert "Ledger: -" in page and "Stronger model's decisions: -" in page


def test_who_answered_lists_every_archived_answer(tmp_path):
    run = make_run(tmp_path)
    assert "Nobody answered a question in this run." in _section(report.render(run), "## Who answered")
    _w(
        run / "steps/04-verify.answer2.json",
        {"approved": True, "by": "Dana", "note": "fine | ok", "answered_at": "2026-10-14T10:00:00+00:00"},
    )
    _w(run / "steps/05-review.answer1.json", {"decision": "retry", "guidance": "two bookmarks", "by": "Oleg"})
    rows = _rows(_section(report.render(run), "## Who answered"))
    assert rows == [
        "| verify | 2 | Dana | approve | fine \\| ok | 2026-10-14T10:00:00+00:00 |",
        "| review | 1 | Oleg | retry | two bookmarks | - |",
    ]


def test_more_than_thirty_survivors_lists_changed_lines_first(tmp_path):
    page = report.render(make_run(tmp_path))
    survivors = _rows(_section(page, "#### generated: 35 survived"))
    assert len(survivors) == 33
    assert all("**changed line**" in row for row in survivors[:3])
    assert all(row.endswith("| no |") for row in survivors[3:])
    assert "| m.other_29 | 129 | no |" in page and "m.other_30" not in page
    assert "2 more surviving mutants not on changed lines were left out." in page
    assert "| generated | 37 | 2 | 0.0541 | 5 | 2 | 0.4 |" in page


def test_missing_mutation_report(tmp_path):
    page = report.render(make_run(tmp_path, with_mutation=False))
    assert "No mutation numbers in the final round." in page
    assert "No mutation report in the final round." in page


def test_cli_writes_report_md(tmp_path, capsys):
    run = make_run(tmp_path)
    assert cli.main(["report", str(run)]) == 0
    assert capsys.readouterr().out.strip() == str(run / "report.md")
    assert (run / "report.md").read_text().startswith("# t-1: A ticket")
    assert not (run / "summary.json").exists()


def test_cli_out_puts_links_relative_to_the_page(tmp_path):
    run = make_run(tmp_path)
    target = tmp_path / "pages" / "page.md"
    assert cli.main(["report", str(run), "--out", str(target)]) == 0
    assert "[TC-here.md](../t-1/verify/testcases/area/TC-here.md)" in target.read_text()
    assert not (run / "report.md").exists()


def test_a_folder_without_steps_exits_2(tmp_path):
    buf = io.StringIO()
    assert report.main(str(tmp_path), out=buf) == 2
    assert "not a run folder" in buf.getvalue()
    assert cli.main(["report", str(tmp_path)]) == 2
    assert not (tmp_path / "report.md").exists()


def test_a_failed_cases_call_after_a_passed_verify_says_the_cases_were_not_finished(tmp_path):
    run = make_run(tmp_path)
    _w(
        run / "steps/04-verify.json",
        {
            "step": "verify",
            "status": "pass",
            "output": {"reason": "every check passed; approved by the factory"},
        },
    )
    _w(
        run / "verify/test_cases.json",
        {"status": "fail", "reason": "spend cap reached: the test case writer"},
    )
    cases = _section(report.render(run), "## Readable test cases")
    assert "The readable cases were not finished: spend cap reached: the test case writer" in cases
    assert "- area/TC-here.md" in cases
    assert "approved by the factory" not in cases and "No readable cases" not in cases


def test_a_cases_call_stopped_at_the_spend_cap_says_so(tmp_path):
    run = make_run(tmp_path)
    shutil.rmtree(run / "verify" / "testcases", ignore_errors=True)
    _w(
        run / "verify/test_cases.json",
        {"status": "fail", "reason": "spend cap reached: 15.00 of 15.00 USD", "cap_reached": True},
    )
    cases = _section(report.render(run), "## Readable test cases")
    assert (
        "The run stopped at the spend cap before the readable cases were finished: "
        "spend cap reached: 15.00 of 15.00 USD"
    ) in cases
    assert "Case files found" not in cases and "were not finished:" not in cases
