"""Step functions that make no model calls and touch no application, for proving an engine.

Each stub sleeps for the ticket's `stub.sleep_s.<step>` seconds (default 0), appends one line to
`<run folder>/stub_calls.log` when it starts and when it ends, and passes. Verify asks a person when
the ticket sets `"gate": "person"`, and passes or fails on the answer, as the real Verify does.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from factory.driver import STEP_NAMES
from factory.envelope import Gate, StepOutput


def _log(run_dir: str, name: str, event: str) -> None:
    with (Path(run_dir) / "stub_calls.log").open("a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {name} {event} pid={os.getpid()}\n")


def _make(name: str):
    def run(step_input: dict) -> StepOutput:
        ticket, run_dir = step_input["ticket"], step_input["run_dir"]
        _log(run_dir, name, "start")
        time.sleep(float(((ticket.get("stub") or {}).get("sleep_s") or {}).get(name, 0)))
        answer_path = step_input["artifacts"].get("answer")
        if name == "verify" and ticket.get("gate") == "person":
            if not answer_path:
                _log(run_dir, name, "asks a person")
                gate = Gate(who="Oleg", question="Approve the stub tests?", context={"tests": 0})
                return StepOutput(status="needs_person", gate=gate)
            answer = json.loads(Path(answer_path).read_text())
            if not answer.get("approved"):
                _log(run_dir, name, "declined")
                return StepOutput(status="fail", reason=f"declined: {answer.get('note', '')}")
        _log(run_dir, name, "end")
        return StepOutput(status="pass", artifacts={name: f"{run_dir}/{name}.stub"})

    return run


STEPS = {name: _make(name) for name in STEP_NAMES}
