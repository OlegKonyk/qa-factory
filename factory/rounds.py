"""Per-ticket record of model rounds and spend, kept in <run_dir>/rounds.json.

The file survives re-runs of the driver, so a failed Verify re-run does not get fresh caps.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_CAPS = {"writer_rounds": 3, "advice": 2, "usd": 15.0}
MIN_CALL_USD = 0.50  # a cold headless call costs about 0.10 USD; below this, do not start one
WRITER_ROUND_KINDS = ("repair", "guided", "review_fix")


class CapReached(Exception):
    """A model call would exceed the ticket's spend cap."""


def caps_for(ticket: dict, app: dict) -> dict:
    """DEFAULT_CAPS, overridden by the app's caps, overridden by the ticket's. Unknown keys kept."""
    return {**DEFAULT_CAPS, **(app.get("caps") or {}), **(ticket.get("caps") or {})}


class Ledger:
    def __init__(self, run_dir, caps: dict | None = None):
        self.path = Path(run_dir) / "rounds.json"
        self.entries: list[dict] = []
        file_caps = self._refresh()
        self.caps = dict(caps or file_caps or DEFAULT_CAPS)

    def _refresh(self) -> dict | None:
        """Reload the entries from the file, so two Ledgers on one run folder never lose each other's
        calls (Review holds one while Verify's fix round writes through another). Returns the file's caps.
        """
        if not self.path.is_file():
            return None
        saved = json.loads(self.path.read_text())
        self.entries = list(saved.get("entries") or [])
        return saved.get("caps")

    def add(
        self,
        step: str,
        kind: str,
        cost_usd: float,
        model: str = "",
        duration_s: float = 0.0,
        round: int | None = None,
        outcome: str = "",
    ) -> dict:
        entry = {
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
            "step": step,
            "kind": kind,
            "round": round,
            "cost_usd": cost_usd,
            "model": model,
            "duration_s": duration_s,
            "outcome": outcome,
        }
        self._refresh()
        self.entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"caps": self.caps, "entries": self.entries, "spent_usd": round_4(self._sum())}
        self.path.write_text(json.dumps(data, indent=1))
        return entry

    def spent(self) -> float:
        self._refresh()
        return self._sum()

    def _sum(self) -> float:
        return sum(float(e.get("cost_usd") or 0.0) for e in self.entries)

    def count(self, *kinds: str) -> int:
        self._refresh()
        return sum(1 for e in self.entries if e.get("kind") in kinds)

    def rounds_left(self) -> int:
        return max(0, self.caps["writer_rounds"] - self.count(*WRITER_ROUND_KINDS))

    def advice_left(self) -> int:
        return max(0, self.caps["advice"] - self.count("advice"))

    def budget_for(self, default_usd: float, minimum: float = MIN_CALL_USD) -> float:
        """The --max-budget-usd for the next call; raises CapReached when less than `minimum` is left.

        A call stops at the first turn that goes past its budget, so it can overshoot by one turn.
        """
        spent, cap = self.spent(), float(self.caps["usd"])
        budget = round(min(default_usd, cap - spent), 2)
        if budget < minimum:
            raise CapReached(f"spend cap reached: {spent:.2f} of {cap:.2f} USD spent on this ticket")
        return budget

    def summary(self) -> dict:
        return {
            "caps": self.caps,
            "spent_usd": round_4(self.spent()),
            "writer_rounds_used": self.count(*WRITER_ROUND_KINDS),
            "advice_used": self.count("advice"),
            "calls": len(self.entries),
        }


def round_4(value: float) -> float:
    return round(value, 4)
