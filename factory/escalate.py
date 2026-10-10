"""Ask a stronger model what to do about a check that still fails after the writer's repair round."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from factory import headless

MODEL = os.environ.get("QA_FACTORY_ADVICE_MODEL", "claude-fable-5-1")
BUDGET_USD = float(os.environ.get("QA_FACTORY_ADVICE_BUDGET", "3.00"))
# Below this, do not start a call: it cannot finish. Measured 2026-10-10: a cold one-file call cost
# 0.61 USD; on linkding 573b6f5 a call given 0.75 USD stopped after 4 turns at 1.10 USD, unanswered.
MIN_USD = 1.50
TOOLS = "Read,Glob,Grep"
DECISIONS = ("retry", "change_is_wrong", "environment", "cannot_decide")


def _schema(allowed: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": allowed},
            "why": {"type": "string"},
            "guidance": {"type": "string"},
            "diagnosis": {"type": "string"},
        },
        "required": ["decision", "why", "guidance", "diagnosis"],
    }


def decide(
    *,
    ticket: dict,
    strategy: str,
    diff: str,
    failure: dict,
    history: list[dict],
    test_files: list[str],
    head_tree: str,
    run_dir: str,
    allow_retry: bool,
    budget_usd: float,
    out_path: str,
    runner=subprocess.run,
) -> dict:
    allowed = [d for d in DECISIONS if allow_retry or d != "retry"]
    prompt = (
        (headless.PROMPTS_DIR / "escalate.md")
        .read_text()
        .format_map(
            {
                "ticket_json": json.dumps(ticket, indent=1),
                "strategy": strategy,
                "diff": diff,
                "check": failure.get("check", ""),
                "reason": failure.get("reason", ""),
                "report": failure.get("report", ""),
                "history_json": json.dumps(history, indent=1),
                "test_files": "\n".join(f"- {p}" for p in test_files),
                "run_dir": run_dir,
                "decisions": ", ".join(allowed),
            }
        )
    )
    result = headless.call(
        prompt,
        cwd=head_tree,
        model=MODEL,
        budget_usd=budget_usd,
        tools=TOOLS,
        allowed_tools=TOOLS,
        schema=_schema(allowed),
        add_dirs=[run_dir],
        runner=runner,
    )
    answer = result.structured if isinstance(result.structured, dict) else {}
    if result.is_error or answer.get("decision") not in allowed:
        reason = result.text or result.stderr or ""
        answer = {
            "decision": "cannot_decide",
            "why": "the stronger model gave no usable answer: " + reason[:300],
            "guidance": "",
            "diagnosis": "",
        }
    record = {
        "decision": answer["decision"],
        "why": answer.get("why", ""),
        "guidance": answer.get("guidance", ""),
        "diagnosis": answer.get("diagnosis", ""),
        "allowed": allowed,
        "failure": failure,
        "history": history,
        "metrics": result.metrics(),
        "is_error": result.is_error,
        "model": MODEL,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1))
    return record
