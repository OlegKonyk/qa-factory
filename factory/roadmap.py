"""Reads docs/roadmap.md and reports the state of each item: planned, in progress, done or dropped."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TextIO

STATES = ("planned", "in progress", "done", "dropped")
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "docs" / "roadmap.md"

_GROUP = re.compile(r"^## (Now|Next|Later)\b")
_ITEM = re.compile(r"^### (\d+)\. (.+)$")
_STATE = re.compile(r"^State: (.*)$")


@dataclass
class Item:
    number: int
    title: str
    group: str  # now | next | later
    state: str  # one of STATES
    note: str


class RoadmapError(ValueError):
    """The roadmap file breaks the structure this module reads."""


def _split_state(text: str, label: str) -> tuple[str, str]:
    """(state, note) from the text after `State:`; the longest state word matching wins."""
    text = text.strip()
    for state in sorted(STATES, key=len, reverse=True):
        if text == state or (text.startswith(state) and not text[len(state)].isalnum()):
            return state, text[len(state) :].lstrip(", ").strip()
    raise RoadmapError(f"{label}: unknown state {text!r}, expected one of {', '.join(STATES)}")


def parse(text: str) -> list[Item]:
    """The items of a roadmap text, in file order. Raises RoadmapError on a broken structure."""
    # Each entry: [number, title, group, state line or None]
    raw: list[list] = []
    group: str | None = None
    current: list | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            match = _GROUP.match(line)
            group = match.group(1).lower() if match else None
            current = None
            continue
        match = _ITEM.match(line)
        if match:
            number, title = int(match.group(1)), match.group(2).strip()
            if group is None:
                raise RoadmapError(f"item {number} ({title}) is outside a Now, Next or Later group")
            current = [number, title, group, None]
            raw.append(current)
            continue
        if line.startswith("### "):
            current = None
            continue
        match = _STATE.match(line)
        if match and current is not None and current[3] is None:
            current[3] = match.group(1)
    numbers = [r[0] for r in raw]
    if numbers != list(range(1, len(raw) + 1)):
        raise RoadmapError(f"item numbers must be exactly 1..{len(raw)} in order, found {numbers}")
    items = []
    for number, title, grp, state_text in raw:
        label = f"item {number} ({title})"
        if state_text is None:
            raise RoadmapError(f"{label} has no State: line")
        state, note = _split_state(state_text, label)
        items.append(Item(number, title, grp, state, note))
    return items


def load(path: Path | str | None = None) -> list[Item]:
    """Parse the roadmap file at `path` (default: docs/roadmap.md in this repository)."""
    return parse(Path(path or DEFAULT_PATH).read_text())


def render(items: list[Item]) -> str:
    """A plain-text table, one line per item, then a line counting the items by state."""
    rows = [["#", "group", "state", "title", "note"]]
    rows += [[str(i.number), i.group, i.state, i.title, i.note] for i in items]
    widths = [max(len(r[c]) for r in rows) for c in range(5)]
    lines = ["  ".join(cell.ljust(widths[c]) for c, cell in enumerate(r)).rstrip() for r in rows]
    counts = [f"{n} {s}" for s in STATES if (n := sum(1 for i in items if i.state == s))]
    lines.append(f"{len(items)} items: {', '.join(counts)}")
    return "\n".join(lines) + "\n"


def main(path: str | None = None, as_json: bool = False, out: TextIO | None = None) -> int:
    """Print the roadmap's per-item state (a table, or JSON); 1 when the file cannot be read."""
    out = out or sys.stdout
    try:
        items = load(path)
    except (RoadmapError, OSError) as exc:
        out.write(f"roadmap: {exc}\n")
        return 1
    if as_json:
        out.write(json.dumps([asdict(i) for i in items], indent=2) + "\n")
    else:
        out.write(render(items))
    return 0
