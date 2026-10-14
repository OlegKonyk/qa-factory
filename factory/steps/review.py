"""Step: review the generated tests for ways they could mislead.

When the review asks for changes, the test writer gets its findings for one fix round
(`verify.repair_from_review`: Verify's checks run again) and the review runs once more. When it
still asks for changes, or no writer round is left for a fix, it stops for a person (gate `review`):
`sign_off`, `another_round` or `decline`. Under the `person` mode an approving review stops too.
"""

import json
from pathlib import Path

from factory import gates, rounds
from factory.headless import one_prompt
from factory.steps import verify
from factory.steps.ship import restore_tests

SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "summary": {"type": "string"},
                    "failure_scenario": {"type": "string"},
                },
                "required": ["file", "line", "severity", "summary", "failure_scenario"],
            },
        },
        "verdict": {"type": "string", "enum": ["approve", "request_changes"]},
    },
    "required": ["findings", "verdict"],
}


SIGN_OFF = {
    "decision": "sign_off",
    "means": "the tests go on to Ship as they are; the note is kept in the step's reason",
    "carries": "note",
}
DECLINE = {"decision": "decline", "means": "the step fails with the note as its reason"}
REVIEW_ANSWERS = [
    SIGN_OFF,
    {
        "decision": "another_round",
        "means": "one more fix round on the findings, then review again, when a writer round is left; "
        "otherwise the step fails",
    },
    DECLINE,
]


def _test_files(inp: dict) -> str:
    manifest = (inp.get("artifacts") or {}).get("tests_manifest")
    if manifest and Path(manifest).is_file():
        files = json.loads(Path(manifest).read_text()).get("files", [])
        return "\n".join(files)
    return "(none named; review the diff)"


def _review(inp: dict, ledger, kwargs) -> dict:
    out = one_prompt(
        "review",
        inp,
        SCHEMA,
        "claude-opus-5-5",
        ledger.budget_for(1.00),
        "Read,Glob,Grep",
        "Read,Glob,Grep",
        extra={"test_files": _test_files(inp)},
        allow_blind=False,  # the reviewer always sees the change
        **kwargs,
    )
    m = out.get("metrics") or {}
    ledger.add(
        "review",
        "review",
        float(m.get("cost_usd") or 0.0),
        m.get("model") or "",
        (m.get("duration_ms") or 0) / 1000,
    )
    return out


def _verdict(out: dict) -> tuple[dict, list[str]]:
    data = json.loads(Path(out["artifacts"]["review"]).read_text())["structured"]
    high = [f for f in data.get("findings", []) if f.get("severity") == "high"]
    return data, [f"{f['file']}:{f['line']} {f['summary']}" for f in high]


def _round_key(path: Path) -> str:
    """`review.round2.json` -> `review_round2`, the artifact name of an earlier review."""
    return "review_" + path.stem.split(".")[-1]


def _next_round(run_dir) -> Path:
    folder = Path(run_dir) / "review"
    k = 1
    while (folder / f"review.round{k}.json").exists():
        k += 1
    return folder / f"review.round{k}.json"


def _latest_round(run_dir) -> Path:
    """The newest earlier review, `review/review.roundK.json`; round 1 when there is none yet."""
    nxt = _next_round(run_dir)
    k = int(nxt.stem.split("round")[-1])
    return nxt.with_name(f"review.round{max(k - 1, 1)}.json")


def _settle(inp: dict, out: dict, reason: str) -> dict:
    """A review that passed its call: stop for a person on changes requested, or under `person`."""
    data, lines = _verdict(out)
    ticket, app = inp["ticket"], inp["repo"]["app"]
    title = ticket.get("title", ticket.get("id"))
    changes = data.get("verdict") == "request_changes"
    if not changes and gates.mode_for("review", ticket, app) != "person":
        return out
    if changes:
        reason = reason + ": " + ("; ".join(lines) or "no high findings listed")
        question = f"The review of the tests for '{title}' {reason.removeprefix('review ')}"
        answers = REVIEW_ANSWERS
    else:
        reason = "the review approves; review mode is person"
        question = f"The review approves the tests for '{title}'; sign them off for Ship?"
        answers = [SIGN_OFF, DECLINE]
    ledger = rounds.Ledger(inp["run_dir"], rounds.caps_for(ticket, app))
    return {
        **out,
        "status": "needs_person",
        "reason": reason,
        "gate": {
            "kind": "review",
            "who": gates.approver(app),
            "question": question,
            "context": {
                "verdict": data.get("verdict"),
                "findings": data.get("findings") or [],
                "review": out["artifacts"].get("review"),
                "writer_rounds_left": ledger.rounds_left(),
            },
            "answers": answers,
        },
    }


def _fail(reason: str) -> dict:
    return {"status": "fail", "artifacts": {}, "reason": reason, "gate": None, "metrics": {}}


def _load(path) -> dict | None:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, TypeError, ValueError):
        return None


def _review_again(inp: dict, fix: dict, earlier: Path, ledger, kwargs, carried: dict | None = None) -> dict:
    """After the fix round passed Verify's checks: review the new tests once more."""
    carried = {**(carried or {}), **(fix.get("artifacts") or {}), _round_key(earlier): str(earlier)}
    again = {**inp, "artifacts": {**(inp.get("artifacts") or {}), **(fix.get("artifacts") or {})}}
    try:
        out = _review(again, ledger, kwargs)
    except rounds.CapReached as e:
        return {**_fail(str(e)), "artifacts": carried}
    out["artifacts"] = {**carried, **out["artifacts"]}
    if out["status"] != "pass":
        return out
    return _settle(again, out, "review still requests changes after the fix round")


def _fix_round(inp: dict, data: dict, carried: dict, ledger, kwargs) -> dict:
    """The writer gets the findings, Verify's checks run again, the review runs again."""
    earlier = _next_round(inp["run_dir"])
    Path(carried["review"]).replace(earlier)
    kept = {k: v for k, v in carried.items() if k != "review"}
    fix = verify.repair_from_review(inp, data)
    if fix["status"] != "pass":
        kept = {**kept, **(fix.get("artifacts") or {}), _round_key(earlier): str(earlier)}
        return {**fix, "reason": "review fix round: " + fix["reason"], "artifacts": kept}
    return _review_again(inp, fix, earlier, ledger, kwargs, kept)


def _answer_review(inp: dict, previous, ledger, kwargs) -> dict:
    """A person answered Review's own gate."""
    answer = gates.read_answer(inp["artifacts"]["answer"])  # the driver checked it against the gate
    by, note = answer["by"], answer.get("note", "")
    recorded = previous.output.to_dict()
    carried = dict(recorded.get("artifacts") or {})
    decision = answer["decision"]
    if decision == "sign_off":
        return {
            "status": "pass",
            "artifacts": carried,
            "reason": f"review signed off by {by}: {note}".strip(),
            "gate": None,
            "metrics": recorded.get("metrics") or {},
        }
    if decision != "another_round":
        return _fail(f"review declined by {by}: {note}".strip())
    if ledger.rounds_left() <= 0:
        why = recorded.get("reason", "")
        return _fail(f"another round asked by {by}, but no writer round is left: {why}")
    base = {k: v for k, v in (inp.get("artifacts") or {}).items() if k != "answer"}
    again = {**inp, "artifacts": {**base, **carried}}
    data = json.loads(Path(carried["review"]).read_text())["structured"]
    return _fix_round(again, data, carried, ledger, kwargs)


def run(inp: dict, runner=None) -> dict:
    kwargs = {"runner": runner} if runner else {}
    artifacts = inp.get("artifacts") or {}
    ledger = rounds.Ledger(inp["run_dir"], rounds.caps_for(inp["ticket"], inp["repo"]["app"]))

    if "answer" in artifacts:
        # Two gates can stop Review: its own (kind `review`), and Verify's, raised in the fix round.
        # The record that asked tells them apart.
        previous = gates.last_record(inp["run_dir"], "review")
        if previous and previous.output.gate and previous.output.gate.kind == "review":
            return _answer_review(inp, previous, ledger, kwargs)
        round1 = _latest_round(inp["run_dir"])
        fix = verify.resume(inp)  # the fix round stopped for a person; Verify reads the answer
        if fix["status"] != "pass":
            carried = {**(fix.get("artifacts") or {}), _round_key(round1): str(round1)}
            return {**fix, "reason": "review fix round: " + fix["reason"], "artifacts": carried}
        return _review_again(inp, fix, round1, ledger, kwargs)

    # Never review, and so never pass to Ship, tests whose checks did not pass: a fix round that
    # failed or stopped leaves Verify's report in that state.
    verify_report = _load(artifacts.get("verify_report")) or {}
    if verify_report.get("status") not in (None, "pass"):
        return _fail(
            f"Verify's checks have not passed on the current tests (status {verify_report['status']}); "
            "re-run Verify for this ticket"
        )

    manifest = artifacts.get("tests_manifest")
    if manifest and Path(manifest).is_file():  # the reviewer reads the tests in the head worktree
        files = json.loads(Path(manifest).read_text()).get("files", [])
        restore_tests(inp["repo"]["head_tree"], files, artifacts.get("tests_dir"))
    try:
        out = _review(inp, ledger, kwargs)
    except rounds.CapReached as e:
        return _fail(str(e))
    if out["status"] != "pass":
        return out
    data, _ = _verdict(out)
    if data.get("verdict") != "request_changes" or ledger.count("review_fix") or ledger.rounds_left() <= 0:
        # Approved, or no fix round left (one per ticket, and only with a writer round left).
        return _settle(inp, out, "review requests changes")
    return _fix_round(inp, data, dict(out["artifacts"]), ledger, kwargs)
