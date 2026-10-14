"""Step: plan the smallest set of new tests, placed by the application's strategy.

It stops for a person (gate `plan`) when the plan says its risk is high or lists patterns the
strategy does not cover (`unknown_patterns`), and always under the `person` mode. The person
answers `approve`, `edit` (an edited plan replaces the artifact) or `decline`.
"""

import json
from pathlib import Path

from factory import gates
from factory.headless import one_prompt

SCHEMA = {
    "type": "object",
    "properties": {
        "tests": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "surface": {"type": "string", "enum": ["api", "browser"]},
                    "file": {"type": "string"},
                    "name": {"type": "string"},
                    "covers": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["surface", "file", "name", "covers", "reason"],
            },
        },
        "placement_reason": {"type": "string"},
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "unknown_patterns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["tests", "placement_reason", "risk", "unknown_patterns"],
}

PLAN_ANSWERS = [
    {"decision": "approve", "means": "the plan stands as written"},
    {
        "decision": "edit",
        "means": "the edited plan replaces the plan: a path to a JSON file in the plan's structured "
        "shape, or to plan/plan.json itself edited in place, or the object inline; the file replaced "
        "is kept as plan.before-edit.json",
        "carries": "plan",
    },
    {"decision": "decline", "means": "the step fails with the note as its reason"},
]


def _gate(inp: dict, out: dict) -> dict:
    if out["status"] != "pass":
        return out
    ticket, app = inp["ticket"], inp["repo"]["app"]
    # `model` is read as `auto` here: only Verify has a stronger model deciding before a person.
    mode = gates.mode_for("plan", ticket, app)
    data = json.loads(Path(out["artifacts"]["plan"]).read_text())["structured"]
    risk = data.get("risk")
    unknown = list(data.get("unknown_patterns") or [])
    if mode != "person" and risk != "high" and not unknown:
        return out
    lines = [f"- risk: {risk}"] if risk == "high" else []
    lines += [f"- not in the strategy: {u}" for u in unknown]
    title = ticket.get("title", ticket.get("id"))
    if lines:
        question = f"The test plan for '{title}' needs a look before tests are written:\n" + "\n".join(lines)
    else:
        question = f"Approve the test plan for '{title}' ({len(data.get('tests') or [])} tests)?"
    return {
        **out,
        "status": "needs_person",
        "reason": "the plan needs a person: " + ("; ".join(lines) or f"plan mode is {mode}"),
        "gate": {
            "kind": "plan",
            "who": gates.approver(app),
            "question": question,
            "context": {
                "risk": risk,
                "unknown_patterns": unknown,
                "tests": data.get("tests") or [],
                "placement_reason": data.get("placement_reason", ""),
                "plan": out["artifacts"]["plan"],
            },
            "answers": PLAN_ANSWERS,
        },
    }


def _edited(value, run_dir: str) -> tuple[dict | None, str]:
    """The edited plan from the answer's `plan` (a path or the object); (None, problem) when unusable.

    A file may hold the structured plan itself or the plan file's own shape (`plan/plan.json`, edited
    in place), whose `structured` is the plan.
    """
    if isinstance(value, str) and value.strip():
        path = Path(value).expanduser()
        if not path.is_absolute() and (Path(run_dir) / path).is_file():
            path = Path(run_dir) / path
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as err:
            return None, f"plan file {path} is not readable JSON: {err}"
        if isinstance(value, dict) and "tests" not in value and isinstance(value.get("structured"), dict):
            value = value["structured"]
    if not isinstance(value, dict) or not isinstance(value.get("tests"), list):
        return None, (
            '"plan" must be the structured plan (an object with a "tests" list, inline or in a file) or '
            'a path to the plan file itself (plan/plan.json, with that object under "structured")'
        )
    return value, ""


def _resume(inp: dict) -> dict:
    answer = gates.read_answer(inp["artifacts"]["answer"])  # the driver checked it against the gate
    by, note = answer["by"], answer.get("note", "")
    previous = gates.last_record(inp["run_dir"], "plan")
    recorded = previous.output.to_dict() if previous else {}
    artifacts = dict(recorded.get("artifacts") or {})
    plan_path = Path(artifacts.setdefault("plan", str(Path(inp["run_dir"]) / "plan" / "plan.json")))
    decision = answer["decision"]
    passed = {"status": "pass", "artifacts": artifacts, "gate": None, "metrics": {}}
    if decision == "approve":
        return {**passed, "reason": f"plan approved by {by}: {note}".strip()}
    if decision != "edit":
        reason = f"plan declined by {by}: {note}".strip()
        return {**passed, "status": "fail", "artifacts": {}, "reason": reason}
    edited, problem = _edited(answer.get("plan"), inp["run_dir"])
    if edited is None:
        if recorded.get("gate"):  # ask again rather than lose the gate: the question stands
            return {**recorded, "reason": f"answer by {by} not used: {problem}"}
        return {**passed, "status": "fail", "artifacts": {}, "reason": problem}
    old = json.loads(plan_path.read_text()) if plan_path.is_file() else {}
    if plan_path.is_file():
        plan_path.replace(plan_path.with_name("plan.before-edit.json"))
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({**old, "structured": edited, "edited_by": by, "note": note}, indent=2))
    return {**passed, "reason": f"plan edited by {by}"}


def run(inp: dict, runner=None) -> dict:
    if "answer" in (inp.get("artifacts") or {}):
        return _resume(inp)
    frame = (inp.get("artifacts") or {}).get("frame")
    frame_json = Path(frame).read_text() if frame and Path(frame).is_file() else ""
    kwargs = {"runner": runner} if runner else {}
    out = one_prompt(
        "plan",
        inp,
        SCHEMA,
        "claude-sonnet-5-5",
        0.50,
        "Read,Glob,Grep",
        "Read,Glob,Grep",
        extra={"frame_json": frame_json},
        **kwargs,
    )
    return _gate(inp, out)
