"""Step: review the generated tests for ways they could mislead."""

import json
from pathlib import Path

from factory.headless import one_prompt
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


def run(inp: dict, runner=None) -> dict:
    kwargs = {"runner": runner} if runner else {}
    manifest = (inp.get("artifacts") or {}).get("tests_manifest")
    if manifest and Path(manifest).is_file():  # the reviewer reads the tests in the head worktree
        files = json.loads(Path(manifest).read_text()).get("files", [])
        restore_tests(inp["repo"]["head_tree"], files, inp["artifacts"].get("tests_dir"))
    out = one_prompt(
        "review",
        inp,
        SCHEMA,
        "claude-opus-5-5",
        1.00,
        "Read,Glob,Grep",
        "Read,Glob,Grep",
        extra={"test_files": _test_files(inp)},
        **kwargs,
    )
    if out["status"] != "pass":
        return out
    data = json.loads(Path(out["artifacts"]["review"]).read_text())["structured"]
    if data.get("verdict") == "request_changes":
        high = [f for f in data.get("findings", []) if f.get("severity") == "high"]
        lines = [f"{f['file']}:{f['line']} {f['summary']}" for f in high]
        out["status"] = "fail"
        out["reason"] = "review requests changes: " + ("; ".join(lines) or "no high findings listed")
    return out
