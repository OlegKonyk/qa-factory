"""Reads a run folder and prints the numbers the exploration compares: tests, mutation, time, spend."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

STEP_NAMES = ["frame", "plan", "implement", "verify", "review", "ship"]
SET_NAMES = ["generated", "generated_and_developers", "developers"]
VERDICT_KEYS = {
    "fail_at_base_on_assertion": "proves-behaviour",
    "pass_on_both": "passes-without-change",
    "missing_name": "missing-name",
    "crash": "crash",
    "head_fails": "head-fails",
}
NUMBER_KEYS = [
    "tests",
    "tests_api",
    "tests_browser",
    "pass_at_head",
    *VERDICT_KEYS,
]


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _result(doc):
    """The report inside a check's dumped JSON, or None for a failure that carries none."""
    if not isinstance(doc, dict):
        return None
    result = doc.get("result")
    return result if isinstance(result, dict) else None


def _is_browser(node_id: str) -> bool:
    return Path(node_id.split("::")[0]).name.startswith("e2e_test_")


def _test_numbers(revert: dict | None) -> dict:
    numbers = dict.fromkeys(NUMBER_KEYS)
    tests = (revert or {}).get("tests")
    if not isinstance(tests, dict):
        return numbers
    verdicts = [t.get("verdict") for t in tests.values()]
    numbers["tests"] = len(tests)
    numbers["tests_browser"] = sum(_is_browser(n) for n in tests)
    numbers["tests_api"] = len(tests) - numbers["tests_browser"]
    numbers["pass_at_head"] = sum(t.get("at_head") == "pass" for t in tests.values())
    for key, verdict in VERDICT_KEYS.items():
        numbers[key] = verdicts.count(verdict)
    return numbers


def _mutation_numbers(mutation: dict | None) -> dict:
    runs = (mutation or {}).get("runs")
    if not isinstance(runs, dict):
        return {}
    out = {}
    for name in [n for n in SET_NAMES if n in runs] + [n for n in runs if n not in SET_NAMES]:
        run = runs[name]
        lines = run.get("on_changed_lines") or {}
        out[name] = {
            "checked": run.get("checked"),
            "killed": run.get("killed"),
            "score": run.get("score"),
            "changed_lines": {k: lines.get(k) for k in ("checked", "killed", "score")},
        }
    return out


def _round_numbers(revert: dict | None, mutation: dict | None) -> dict:
    return {**_test_numbers(revert), "mutation": _mutation_numbers(mutation)}


def _failure_text(failure) -> str | None:
    if isinstance(failure, dict):
        return f"{failure.get('check', '')}: {failure.get('reason', '')}".strip(": ")
    return failure or None


def _rounds(verify: Path, report: dict) -> list[dict]:
    """[{round, kind, failure, revert, mutation}] per round; a run without `rounds` has one."""
    listed = report.get("rounds")
    if not listed:
        return [
            {
                "round": 1,
                "kind": "write",
                "failure": None,
                "revert": _result(_load(verify / "revert.json")),
                "mutation": _result(_load(verify / "mutation.json")),
            }
        ]
    out = []
    for entry in listed:
        folder = verify / "rounds" / str(entry.get("round"))
        out.append(
            {
                "round": entry.get("round"),
                "kind": entry.get("kind"),
                "failure": _failure_text(entry.get("failure")),
                "revert": _result(_load(folder / "revert.json")),
                "mutation": _result(_load(folder / "mutation.json")),
            }
        )
    return out


def _stages(run: Path) -> tuple[dict, dict]:
    stages, records = {}, {}
    steps = run / "steps"
    for index, name in enumerate(STEP_NAMES, start=1):
        rec = _load(steps / f"{index:02d}-{name}.json")
        if not isinstance(rec, dict):
            continue
        records[name] = rec
        metrics = (rec.get("output") or {}).get("metrics") or {}
        earlier = list(steps.glob(f"{index:02d}-{name}.round*.json"))
        # A step resumed from a person's answer records only the resume; its checks' own times say
        # how long the work took. Sub-timings of mutation ("mutation.<set>") are inside "mutation".
        times = metrics.get("time_s") if isinstance(metrics.get("time_s"), dict) else {}
        work_s = sum(
            v for k, v in times.items() if isinstance(v, int | float) and not k.startswith("mutation.")
        )
        stages[name] = {
            "status": rec.get("status"),
            "duration_s": rec.get("duration_s"),
            "work_s": round(work_s, 1) if times else None,
            "cost_usd": metrics.get("cost_usd"),
            "model": metrics.get("model"),
            "earlier_runs": len(earlier),
        }
    return stages, records


def _verify_parts(record: dict | None) -> dict:
    metrics = ((record or {}).get("output") or {}).get("metrics") or {}
    costs = metrics.get("costs") or {}
    return {
        "time_s": metrics.get("time_s") or {},
        "cost_usd": {k: v.get("cost_usd") for k, v in costs.items() if isinstance(v, dict)},
    }


def _ledger(run: Path) -> dict | None:
    data = _load(run / "rounds.json")
    if not isinstance(data, dict):
        return None
    entries = data.get("entries") or []
    writer = ("repair", "guided", "review_fix")
    return {
        "caps": data.get("caps"),
        "spent_usd": data.get("spent_usd"),
        "writer_rounds_used": sum(e.get("kind") in writer for e in entries),
        "advice_used": sum(e.get("kind") == "advice" for e in entries),
        "calls": len(entries),
    }


def _decisions(verify: Path) -> list[str]:
    def number(path: Path) -> int:
        tail = path.stem.rsplit("-", 1)[-1]
        return int(tail) if tail.isdigit() else 0

    out = []
    for path in sorted(verify.glob("escalation-*.json"), key=number):
        doc = _load(path)
        if isinstance(doc, dict) and doc.get("decision"):
            out.append(str(doc["decision"]))
    return out


def summarize(run_dir) -> dict:
    """The comparison numbers of one run folder."""
    run = Path(run_dir)
    verify = run / "verify"
    ticket = _load(run / "ticket.json") or {}
    report = _load(verify / "report.json") or {}
    rounds = _rounds(verify, report)
    stages, records = _stages(run)

    def numbers(r: dict) -> dict:
        return {"round": r["round"], **_round_numbers(r["revert"], r["mutation"])}

    first, final = numbers(rounds[0]), numbers(rounds[-1])
    if len(rounds) == 1:
        final = first
    costs = [s["cost_usd"] for s in stages.values() if s["cost_usd"] is not None]
    return {
        "ticket": ticket.get("id") or run.name,
        "qa_mode": ticket.get("qa_mode") or "sequential",
        "first_round": first,
        "final_round": final,
        "rounds": [{k: r[k] for k in ("round", "kind", "failure")} for r in rounds],
        "decisions": _decisions(verify),
        "stages": stages,
        "verify_parts": _verify_parts(records.get("verify")),
        "spend_usd": round(sum(costs), 4),
        "ledger": _ledger(run),
        "blind_audit": report.get("blind_audit"),
    }


def _cell(value) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return str(round(value, 4))
    return str(value)


def _table(header: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return lines


def _number_rows(summaries: list[dict]) -> list[list]:
    rows = [["qa_mode", *[s["qa_mode"] for s in summaries]]]
    for which in ("first_round", "final_round"):
        rows.append([f"{which} (round number)", *[s[which]["round"] for s in summaries]])
        for key in NUMBER_KEYS:
            rows.append([f"{which} {key}", *[s[which][key] for s in summaries]])
        names = []
        for s in summaries:
            names += [n for n in s[which]["mutation"] if n not in names]
        for name in names:
            for field in ("checked", "killed", "score"):
                rows.append(
                    [
                        f"{which} mutation {name} {field}",
                        *[(s[which]["mutation"].get(name) or {}).get(field) for s in summaries],
                    ]
                )
            for field in ("checked", "killed", "score"):
                rows.append(
                    [
                        f"{which} mutation {name} changed lines {field}",
                        *[
                            ((s[which]["mutation"].get(name) or {}).get("changed_lines") or {}).get(field)
                            for s in summaries
                        ],
                    ]
                )
    rows.append(["spend_usd", *[s["spend_usd"] for s in summaries]])
    return rows


def render(summaries: list[dict]) -> str:
    """Markdown: the numbers table, then per run the stages, rounds and decisions."""
    lines = _table(["number", *[s["ticket"] for s in summaries]], _number_rows(summaries))
    for s in summaries:
        lines += ["", f"### {s['ticket']}: stages", ""]
        rows = [
            [name, st["status"], st["duration_s"], st.get("work_s"), st["cost_usd"], st["model"]]
            for name, st in s["stages"].items()
        ]
        lines += _table(["step", "status", "duration_s", "checks_s", "cost_usd", "model"], rows)
        lines += ["", f"### {s['ticket']}: rounds", ""]
        rows = [[r["round"], r["kind"], r["failure"]] for r in s["rounds"]]
        lines += _table(["round", "kind", "failure"], rows)
        lines += ["", f"Decisions: {', '.join(s['decisions']) or '-'}"]
    return "\n".join(lines) + "\n"


def main(run_dirs: list[str], json_path: str | None = None, out: TextIO | None = None) -> int:
    """Print the summary of one or several runs; write JSON for one run by default."""
    missing = [d for d in run_dirs if not (Path(d) / "steps").is_dir()]
    if missing:
        (out or sys.stderr).write(f"not a run folder (no steps/ inside): {', '.join(missing)}\n")
        return 2
    summaries = [summarize(d) for d in run_dirs]
    (out or sys.stdout).write(render(summaries))
    if json_path is None and len(run_dirs) == 1:
        json_path = str(Path(run_dirs[0]) / "summary.json")
    if json_path:
        data = summaries[0] if len(summaries) == 1 else summaries
        Path(json_path).write_text(json.dumps(data, indent=2) + "\n")
    return 0
