"""Step: plan the smallest set of new tests, placed by the application's strategy."""

from pathlib import Path

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
    },
    "required": ["tests", "placement_reason"],
}


def run(inp: dict, runner=None) -> dict:
    frame = (inp.get("artifacts") or {}).get("frame")
    frame_json = Path(frame).read_text() if frame and Path(frame).is_file() else ""
    kwargs = {"runner": runner} if runner else {}
    return one_prompt(
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
