"""Step: restate the ticket's acceptance criteria as things a test can check.

It stops for a person (gate `clarify`) when a criterion is not testable or the ticket leaves out
what a test writer must know (`missing_contract`), and always under the `person` mode. Ambiguities
alone never stop it. The person answers `proceed` (the frame as read), `clarify` (new ticket fields,
then Frame runs again on the clarified ticket) or `decline`.
"""

import json
from pathlib import Path

from factory import driver, gates
from factory.headless import one_prompt

SCHEMA = {
    "type": "object",
    "properties": {
        "acceptance_criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "testable": {"type": "boolean"},
                    "surface": {"type": "string", "enum": ["api", "browser", "unit", "none"]},
                },
                "required": ["id", "text", "testable", "surface"],
            },
        },
        "ambiguities": {"type": "array", "items": {"type": "string"}},
        "missing_contract": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["acceptance_criteria", "ambiguities", "missing_contract", "summary"],
}

CLARIFY_ANSWERS = [
    {"decision": "proceed", "means": "go on with the ticket as Frame read it"},
    {
        "decision": "clarify",
        "means": "replace the ticket's description, contract or acceptance_criteria with the fields "
        "given, then frame the clarified ticket again",
        "carries": "ticket",
    },
    {"decision": "decline", "means": "the step fails with the note as its reason"},
]


def _call(inp: dict, runner) -> dict:
    kwargs = {"runner": runner} if runner else {}
    return one_prompt(
        "frame", inp, SCHEMA, "claude-sonnet-5-5", 0.50, "Read,Glob,Grep", "Read,Glob,Grep", **kwargs
    )


def _gate(inp: dict, out: dict) -> dict:
    """The frame's own rule: stop under `person`, or on an untestable criterion or a missing contract."""
    if out["status"] != "pass":
        return out
    ticket, app = inp["ticket"], inp["repo"]["app"]
    # `model` is read as `auto` here: only Verify has a stronger model deciding before a person.
    mode = gates.mode_for("frame", ticket, app)
    data = json.loads(Path(out["artifacts"]["frame"]).read_text())["structured"]
    missing = list(data.get("missing_contract") or [])
    untestable = [
        f"{c.get('id', '?')}: {c.get('text', '')}"
        for c in data.get("acceptance_criteria") or []
        if c.get("testable") is False
    ]
    if mode != "person" and not missing and not untestable:
        return out
    lines = [f"- missing from the ticket: {m}" for m in missing]
    lines += [f"- not testable: {u}" for u in untestable]
    if lines:
        question = f"Frame cannot hand '{ticket.get('title', ticket.get('id'))}' to a test writer as is:\n"
        question += "\n".join(lines)
    else:
        question = f"Frame read '{ticket.get('title', ticket.get('id'))}'; go on with it as read?"
    return {
        **out,
        "status": "needs_person",
        "reason": "the ticket needs a person: " + ("; ".join(lines) or f"frame mode is {mode}"),
        "gate": {
            "kind": "clarify",
            "who": gates.approver(app),
            "question": question,
            "context": {
                "missing_contract": missing,
                "untestable": untestable,
                "ambiguities": list(data.get("ambiguities") or []),
                "frame": out["artifacts"]["frame"],
            },
            "answers": CLARIFY_ANSWERS,
        },
    }


def _resume(inp: dict, runner) -> dict:
    answer = gates.read_answer(inp["artifacts"]["answer"])  # the driver checked it against the gate
    by, note = answer["by"], answer.get("note", "")
    previous = gates.last_record(inp["run_dir"], "frame")
    recorded = previous.output.to_dict() if previous else {}
    artifacts = dict(recorded.get("artifacts") or {})
    artifacts.setdefault("frame", str(Path(inp["run_dir"]) / "frame" / "frame.json"))
    decision = answer["decision"]
    if decision == "proceed":
        return {
            "status": "pass",
            "artifacts": artifacts,
            "reason": f"proceeded as read by {by}: {note}".strip(),
            "gate": None,
            "metrics": {},
        }
    if decision != "clarify":
        return {
            "status": "fail",
            "artifacts": {},
            "reason": f"declined by {by}: {note}".strip(),
            "gate": None,
            "metrics": {},
        }
    fields = answer.get("ticket")
    problem = None
    if not isinstance(fields, dict) or not fields:
        problem = f'"clarify" needs a "ticket" object with any of {", ".join(driver.CLARIFIABLE)}'
    elif set(fields) - set(driver.CLARIFIABLE):
        foreign = ", ".join(sorted(set(fields) - set(driver.CLARIFIABLE)))
        problem = f'"ticket" may only replace {", ".join(driver.CLARIFIABLE)}; found {foreign}'
    if problem and recorded.get("gate"):  # ask again rather than lose the gate: the question stands
        return {**recorded, "reason": f"answer by {by} not used: {problem}"}
    if problem:
        return {"status": "fail", "artifacts": {}, "reason": problem, "gate": None, "metrics": {}}
    path = Path(inp["run_dir"]) / driver.CLARIFIED_FILE
    earlier = json.loads(path.read_text()) if path.exists() else {}
    path.write_text(json.dumps({**earlier, **fields}, indent=2) + "\n")
    clarified = {**inp, "ticket": {**inp["ticket"], **earlier, **fields}}
    clarified["artifacts"] = {k: v for k, v in inp["artifacts"].items() if k != "answer"}
    return _gate(clarified, _call(clarified, runner))


def run(inp: dict, runner=None) -> dict:
    if "answer" in (inp.get("artifacts") or {}):
        return _resume(inp, runner)
    return _gate(inp, _call(inp, runner))
