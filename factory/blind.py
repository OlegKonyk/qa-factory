"""Blind mode: QA sessions that work from the ticket and the code before the change only.

A ticket with "qa_mode": "blind" has Frame, Plan and the first test writer run in the base worktree.
The helpers here build what hides the change from them: a ticket without its provenance, the list
of paths they must not read, the Claude Code settings that deny those paths and git, and an audit of
a session's transcript that proves the denial held.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

HIDDEN_FIELDS = ("base", "head", "source", "app", "caps", "gate", "qa_mode")

WHERE_SEQUENTIAL = "You are in the working tree of the changed code. You may read the developers' own tests."
WHERE_BLIND = (
    "You are in the working tree of the code before the change. The change does not exist yet and "
    "you cannot see it; there are no developers' tests for it. Work from the ticket and the code as "
    "it is now, and do not look for the change anywhere else."
)

_GIT_COMMAND = re.compile(r"^\s*(?:cd\s+\S+\s*&&\s*)?git(?:\s|$)")


def is_blind(ticket: dict) -> bool:
    """True when the ticket asks for tests written without seeing the change."""
    return ticket.get("qa_mode") == "blind"


def public_ticket(ticket: dict) -> dict:
    """The ticket as a blind session sees it: without HIDDEN_FIELDS (the commits and the provenance
    would point at the change)."""
    return {k: v for k, v in ticket.items() if k not in HIDDEN_FIELDS}


def _resolved(path) -> str:
    return str(Path(path).expanduser().resolve())


def hidden_paths(repo: dict, factory_root) -> list[str]:
    """Absolute, resolved paths a blind session must not read.

    The application's clone, this ticket's head tree, every other ticket's trees under the worktrees
    folder, and the factory's own repository (run folders hold earlier tests). Never the base tree.
    """
    base = _resolved(repo["base_tree"])
    found = {_resolved(repo["app"]["repo"]), _resolved(repo["head_tree"]), _resolved(factory_root)}
    worktrees = Path(repo["app"]["worktrees"]).expanduser()
    if worktrees.is_dir():
        for tree in worktrees.glob("*/*"):
            if tree.is_dir():
                found.add(_resolved(tree))
    found.discard(base)
    return sorted(found)


def settings(hidden: list[str], base: dict | None = None) -> dict:
    """Claude Code settings that deny a blind session the hidden paths and git."""
    out = copy.deepcopy(base) if base else {}
    deny = out.setdefault("permissions", {}).setdefault("deny", [])
    wanted = []
    for p in hidden:
        # p is absolute, so "/" + p gives the double slash Claude Code needs for an absolute path.
        wanted += [f"{tool}(/{p}/**)" for tool in ("Read", "Grep", "Glob", "Edit", "Write")]
    wanted += ["Bash(git *)", "Bash(git)"]
    for entry in wanted:
        if entry not in deny:
            deny.append(entry)
    return out


def _tool_calls(transcript_path):
    for line in Path(transcript_path).read_text().splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "assistant":
            continue
        message = obj.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for item in content if isinstance(content, list) else []:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                yield item


def audit(transcript_path, hidden: list[str], allowed: list[str] = ()) -> dict:
    """Report every tool call in a stream-json transcript that named a hidden path or ran git.

    `allowed` are exact strings a call may name although they lie under a hidden path: the
    application's interpreter, which lives in its clone's virtual environment and which the writer
    is told to run.
    """
    report = {"tool_calls": 0, "flagged": [], "clean": False, "transcript": str(transcript_path)}
    if not Path(transcript_path).is_file():
        report["error"] = "no transcript"
        return report
    for call in _tool_calls(transcript_path):
        report["tool_calls"] += 1
        tool_input = call.get("input")
        dumped = json.dumps(tool_input)
        named = dumped
        for exact in allowed:
            named = named.replace(exact, "")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        ran_git = call.get("name") == "Bash" and isinstance(command, str) and _GIT_COMMAND.match(command)
        if ran_git or any(p in named for p in hidden):
            report["flagged"].append({"tool": call.get("name"), "input": dumped[:300]})
    report["clean"] = not report["flagged"]
    return report
