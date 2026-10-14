"""Writes one Markdown page per run folder: the QA evidence of one ticket, read from its records."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TextIO

from factory import gates, summary
from factory.summary import STEP_NAMES, _cell, _load, _result, _rounds, _table

VERDICT_WORDS = {
    "proves-behaviour": "fails on the old code: proves the change",
    "passes-without-change": "passes on the old code too: proves nothing",
    "missing-name": "fails on the old code only for a name the change adds",
    "crash": "crashed on the old code",
    "head-fails": "fails with the change",
    "skip": "skipped on the old code",
}
SURVIVOR_LIMIT = 30
FAILURE_LIMIT = 300


def _steps(run: Path) -> list[tuple[str, str]]:
    """(step, outcome) for each of the six steps, from the step records."""
    out = []
    for index, name in enumerate(STEP_NAMES, start=1):
        rec = _load(run / "steps" / f"{index:02d}-{name}.json")
        if not isinstance(rec, dict):
            out.append((name, "not run"))
            continue
        status = rec.get("status") or "-"
        output = rec.get("output") or {}
        if status == "fail":
            status = f"fail: {output.get('reason') or '-'}"
        elif status == "needs_person":
            gate = output.get("gate") or {}
            status = f"needs_person: {gate.get('question') or output.get('reason') or '-'}"
        out.append((name, status))
    return out


def _first_line(message, limit: int = 100) -> str:
    lines = str(message or "").strip().splitlines()
    return lines[0][:limit] if lines else ""


def _md(text) -> str:
    """A table cell: pipes escaped, newlines flattened."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def _test_lines(revert: dict | None, final: dict) -> list[str]:
    tests = (revert or {}).get("tests")
    if not isinstance(tests, dict) or not tests:
        lines = ["No revert report in the final round."]
    else:
        rows = []
        for node, t in tests.items():
            file, _, name = node.partition("::")
            rows.append(
                [
                    _md(file),
                    _md(name or "-"),
                    "browser" if summary._is_browser(node) else "API",
                    t.get("at_head"),
                    VERDICT_WORDS.get(t.get("verdict"), t.get("verdict")),
                    _md(_first_line(t.get("message"))),
                ]
            )
        header = ["file", "test", "kind", "with the change", "without the change", "failure on the old code"]
        lines = _table(header, rows)
    counts = [[key, final.get(key)] for key in summary.NUMBER_KEYS]
    return [
        *lines,
        "",
        f"Counts (round {_cell(final.get('round'))}):",
        "",
        *_table(["count", "value"], counts),
    ]


def _developers_lines(run: Path) -> list[str]:
    entry = _load(run / "verify" / "developers_revert.json")
    result = (entry or {}).get("result") if isinstance(entry, dict) else None
    if not result:
        return ["Not run for this ticket (`python -m factory devtests <run folder>` runs it afterwards)."]
    tests = result.get("tests") or {}
    if not tests:
        return [_md(result.get("reason") or "no result")]
    kinds = result.get("kinds") or {}  # absent from results before modified tests were judged: all new
    rows = []
    for node, t in tests.items():
        file, _, name = node.partition("::")
        rows.append(
            [
                _md(file),
                _md(name or "-"),
                kinds.get(node, "new"),
                t.get("at_head"),
                VERDICT_WORDS.get(t.get("verdict"), t.get("verdict")),
                _md(_first_line(t.get("message"))),
            ]
        )
    header = ["file", "test", "kind", "with the change", "without the change", "failure on the old code"]
    return [_md(result.get("reason") or ""), "", *_table(header, rows)]


def _case_title(path: Path) -> str | None:
    try:
        text = path.read_text()
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _case_lines(run: Path, out_dir: Path) -> list[str]:
    verify = run / "verify"
    entry = _load(verify / "test_cases.json")
    if isinstance(entry, dict) and entry.get("status") == "fail":
        # The latest cases call failed (a review's fix round, say) though an earlier Verify passed:
        # say so, and list what it left on disk rather than the passed step's reason.
        found = sorted(
            p.relative_to(verify / "testcases").as_posix() for p in (verify / "testcases").rglob("*.md")
        )
        why = _md(entry.get("reason") or "-")
        if entry.get("cap_reached"):  # resumable: raising caps.usd and running again finishes them
            lines = [f"The run stopped at the spend cap before the readable cases were finished: {why}"]
        else:
            lines = [f"The readable cases were not finished: {why}"]
        if found:
            lines += ["", "Case files found under `verify/testcases/`:", "", *[f"- {_md(f)}" for f in found]]
        return lines
    files = (_result(entry) or {}).get("files")
    if not isinstance(files, list):
        line = "No readable cases were written."
        rec = _load(run / "steps" / "04-verify.json")
        reason = ((rec or {}).get("output") or {}).get("reason") if isinstance(rec, dict) else None
        return [f"{line} Verify ended with: {reason}" if reason else line]
    rows = []
    for name in files:
        # Records hold paths of the machine the run was on; look only inside this folder.
        found = next(
            (
                p
                for p in (verify / "testcases" / name, run.parent / "testcases" / Path(name).name)
                if p.is_file()
            ),
            None,
        )
        if found is None:
            rows.append([_md(name), "-", "not in this folder"])
            continue
        link = Path(os.path.relpath(found, out_dir)).as_posix()
        rows.append([_md(name), _md(_case_title(found) or "-"), f"[{Path(name).name}]({link})"])
    return _table(["case", "title", "link"], rows)


def _survivor_lines(mutation: dict | None) -> list[str]:
    runs = (mutation or {}).get("runs")
    if not isinstance(runs, dict):
        return ["No mutation report in the final round."]
    lines = []
    for name in [n for n in summary.SET_NAMES if n in runs] + [n for n in runs if n not in summary.SET_NAMES]:
        mutants = (runs[name] or {}).get("mutants") or {}
        survived = [
            (k, m) for k, m in mutants.items() if isinstance(m, dict) and m.get("status") == "survived"
        ]
        changed = [(k, m) for k, m in survived if m.get("changed_line")]
        others = [(k, m) for k, m in survived if not m.get("changed_line")]
        left_out = max(0, len(others) - SURVIVOR_LIMIT) if len(survived) > SURVIVOR_LIMIT else 0
        others = others[: len(others) - left_out]
        lines += ["", f"#### {name}: {len(survived)} survived", ""]
        if not survived:
            continue
        rows = [[_md(k), m.get("line"), "**changed line**"] for k, m in changed]
        rows += [[_md(k), m.get("line"), "no"] for k, m in others]
        lines += _table(["mutant", "source line", "on a changed line"], rows)
        if left_out:
            lines += ["", f"{left_out} more surviving mutants not on changed lines were left out."]
    return lines


def _mutation_lines(final: dict, mutation: dict | None) -> list[str]:
    sets = final.get("mutation") or {}
    rows = [
        [
            name,
            m.get("checked"),
            m.get("killed"),
            m.get("score"),
            (m.get("changed_lines") or {}).get("checked"),
            (m.get("changed_lines") or {}).get("killed"),
            (m.get("changed_lines") or {}).get("score"),
        ]
        for name, m in sets.items()
    ]
    header = ["set", "checked", "killed", "score", "changed lines checked", "killed", "score"]
    head = _table(header, rows) if rows else ["No mutation numbers in the final round."]
    return [*head, "", "### Surviving mutants", *_survivor_lines(mutation)]


def _round_lines(s: dict) -> list[str]:
    def failure(text) -> str:
        text = str(text or "-")
        return _md(text if len(text) <= FAILURE_LIMIT else text[:FAILURE_LIMIT] + " ...")

    lines = _table(
        ["round", "kind", "failure"], [[r["round"], r["kind"], failure(r["failure"])] for r in s["rounds"]]
    )
    lines += ["", f"Stronger model's decisions: {', '.join(s['decisions']) or '-'}", ""]
    ledger = s.get("ledger")
    if not ledger:
        return [*lines, "Ledger: -"]
    caps = ledger.get("caps") or {}
    caps_text = (
        ", ".join(f"{k} {_cell(v)}" for k, v in caps.items()) if isinstance(caps, dict) else _cell(caps)
    )
    rows = [
        ["caps", caps_text or "-"],
        ["writer rounds used", ledger.get("writer_rounds_used")],
        ["stronger-model calls used", ledger.get("advice_used")],
        ["model calls in the ledger", ledger.get("calls")],
        ["spent (USD)", ledger.get("spent_usd")],
    ]
    return [*lines, *_table(["ledger", "value"], rows)]


def _stage_lines(s: dict) -> list[str]:
    rows = [
        [name, st["status"], st["duration_s"], st.get("work_s"), st["cost_usd"], st["model"]]
        for name, st in s["stages"].items()
    ]
    header = ["step", "status", "duration (s)", "checks (s)", "cost (USD)", "model"]
    return [
        *_table(header, rows),
        "",
        f"Total spend: {_cell(s['spend_usd'])} USD (measured, from the run's records).",
    ]


def _answer_lines(run: Path) -> list[str]:
    """Every archived answer, `steps/NN-<step>.answerM.json`: the round M of the step it answered."""
    rows = []
    for path in sorted((run / "steps").glob("[0-9][0-9]-*.answer*.json")):
        step, _, rest = path.name[3:].partition(".answer")
        answer = _load(path)
        if not isinstance(answer, dict):
            continue
        rows.append(
            [
                step,
                rest.removesuffix(".json"),
                _md(answer.get("by") or "-"),
                _md(gates.decision_of(answer) or "-"),
                _md(answer.get("note") or answer.get("guidance") or "-"),
                answer.get("answered_at") or "-",
            ]
        )
    if not rows:
        return ["Nobody answered a question in this run."]
    return _table(["step", "round", "by", "decision", "note", "answered at"], rows)


def render(run_dir, out_dir=None) -> str:
    """The Markdown page of one run folder; links are relative to `out_dir` (the run folder by default)."""
    run = Path(run_dir)
    out_dir = Path(out_dir) if out_dir is not None else run
    s = summary.summarize(run)
    ticket = _load(run / "ticket.json") or {}
    report = _load(run / "verify" / "report.json") or {}
    last = _rounds(run / "verify", report)[-1]
    final = s["final_round"]
    outcome = "; ".join(f"{name} {status}" for name, status in _steps(run))
    lines = [
        f"# {s['ticket']}: {ticket.get('title') or '-'}",
        "",
        f"QA mode: {s['qa_mode']}. Steps: {_md(outcome)}.",
        "",
        "## Tests",
        "",
        *_test_lines(last["revert"], final),
        "",
        "## The developers' own tests, written with the change",
        "",
        *_developers_lines(run),
        "",
        "## Readable test cases",
        "",
        *_case_lines(run, out_dir),
        "",
        "## Mutation",
        "",
        *_mutation_lines(final, last["mutation"]),
        "",
        "## Rounds",
        "",
        *_round_lines(s),
        "",
        "## Who answered",
        "",
        *_answer_lines(run),
        "",
        "## Time and spend",
        "",
        *_stage_lines(s),
    ]
    return "\n".join(lines) + "\n"


def main(run_dir: str, out_path: str | None = None, out: TextIO | None = None) -> int:
    """Write the page of one run to `<run_dir>/report.md` (or `out_path`) and print its path."""
    run = Path(run_dir)
    if not (run / "steps").is_dir():
        (out or sys.stderr).write(f"not a run folder (no steps/ inside): {run_dir}\n")
        return 2
    target = Path(out_path) if out_path else run / "report.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(run, target.parent))
    (out or sys.stdout).write(f"{target}\n")
    return 0
