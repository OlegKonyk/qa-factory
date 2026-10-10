"""Step: review the generated tests for ways they could mislead.

When the review asks for changes, the test writer gets its findings for one fix round
(`verify.repair_from_review`: Verify's checks run again) and the review runs once more.
"""

import json
from pathlib import Path

from factory import rounds
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


def _fail(reason: str) -> dict:
    return {"status": "fail", "artifacts": {}, "reason": reason, "gate": None, "metrics": {}}


def _load(path) -> dict | None:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, TypeError, ValueError):
        return None


def _review_again(inp: dict, fix: dict, round1: Path, ledger, kwargs) -> dict:
    """After the fix round passed Verify's checks: review the new tests once more."""
    carried = {**(fix.get("artifacts") or {}), "review_round1": str(round1)}
    again = {**inp, "artifacts": {**(inp.get("artifacts") or {}), **(fix.get("artifacts") or {})}}
    try:
        out = _review(again, ledger, kwargs)
    except rounds.CapReached as e:
        return {**_fail(str(e)), "artifacts": carried}
    out["artifacts"] = {**carried, **out["artifacts"]}
    if out["status"] != "pass":
        return out
    data, lines = _verdict(out)
    if data.get("verdict") == "request_changes":
        out["status"] = "fail"
        out["reason"] = "review still requests changes after the fix round: " + (
            "; ".join(lines) or "no high findings listed"
        )
    return out


def run(inp: dict, runner=None) -> dict:
    kwargs = {"runner": runner} if runner else {}
    artifacts = inp.get("artifacts") or {}
    ledger = rounds.Ledger(inp["run_dir"], rounds.caps_for(inp["ticket"], inp["repo"]["app"]))
    round1 = Path(inp["run_dir"]) / "review" / "review.round1.json"

    if "answer" in artifacts:  # the fix round stopped for a person; Verify reads the answer
        fix = verify.resume(inp)
        if fix["status"] != "pass":
            carried = {**(fix.get("artifacts") or {}), "review_round1": str(round1)}
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
    data, lines = _verdict(out)
    if data.get("verdict") != "request_changes":
        return out
    if ledger.count("review_fix") or ledger.rounds_left() <= 0:
        out["status"] = "fail"
        out["reason"] = "review requests changes: " + ("; ".join(lines) or "no high findings listed")
        return out

    # One fix round: the writer gets the findings, Verify's checks run again, the review runs again.
    Path(out["artifacts"]["review"]).replace(round1)
    fix = verify.repair_from_review(inp, data)
    if fix["status"] != "pass":
        carried = {**(fix.get("artifacts") or {}), "review_round1": str(round1)}
        return {**fix, "reason": "review fix round: " + fix["reason"], "artifacts": carried}
    return _review_again(inp, fix, round1, ledger, kwargs)
