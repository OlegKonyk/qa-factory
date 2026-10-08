"""Step: restate the ticket's acceptance criteria as things a test can check."""

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
        "summary": {"type": "string"},
    },
    "required": ["acceptance_criteria", "ambiguities", "summary"],
}


def run(inp: dict, runner=None) -> dict:
    kwargs = {"runner": runner} if runner else {}
    return one_prompt(
        "frame", inp, SCHEMA, "claude-sonnet-5-5", 0.50, "Read,Glob,Grep", "Read,Glob,Grep", **kwargs
    )
