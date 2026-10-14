"""Where a run stops for a person: the mode of each step, the answer file, telling, and the waiting list.

Every function takes its collaborators as arguments (the process runner, the HTTP opener, the PATH
lookup), so the tests run them with fakes and nothing is shown or sent.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import TextIO

from factory.envelope import Gate, StepRecord

MODES = ("auto", "model", "person")
# `model`: a stronger model decides before a person. Built for Verify only; elsewhere it is read as
# `auto` until a step builds its own.
DEFAULT_MODES = {"verify": "model"}
DEFAULT_APPROVER = "Oleg"
QUESTION_CHARS = 100
NOTIFY_CHARS = 200
POST_TIMEOUT_S = 5


class AnswerError(ValueError):
    """An answer file the driver must not consume: a field is missing, unknown or malformed."""


def _mode(value, where: str) -> str:
    if value not in MODES:
        raise ValueError(f"{where} must be one of {MODES}, got {value!r}")
    return value


def mode_for(step: str, ticket: dict, app: dict) -> str:
    """The step's mode: the ticket's `gates.<step>`, then the recipe's, then the default.

    The single legacy `"gate": "person"` field means `gates.verify: person` (any value but `auto`
    stopped Verify before, and still does); within one file `gates.verify` wins over it.
    """
    for source, where in ((ticket or {}, "ticket"), (app or {}, "recipe")):
        gates = source.get("gates") or {}
        if step in gates:
            return _mode(gates[step], f"{where} gates.{step}")
        if step == "verify" and source.get("gate"):
            return "auto" if source["gate"] == "auto" else "person"
    return DEFAULT_MODES.get(step, "auto")


def approver(app: dict) -> str:
    """Who is asked: the recipe's `approver`, by default Oleg."""
    return (app or {}).get("approver") or DEFAULT_APPROVER


def decision_of(answer: dict) -> str | None:
    """The answer's decision; the old `{"approved": true|false}` form maps to approve/decline."""
    if answer.get("decision") is not None:
        return answer["decision"]
    if answer.get("approved") is True:
        return "approve"
    if answer.get("approved") is False:
        return "decline"
    return None


def read_answer(path, answers: list[dict] | None = None) -> dict:
    """The answer file with its `decision` filled in; raises AnswerError when it must not be consumed.

    `by` is required. `answers` is the gate's accepted answers; when given (non-empty), the decision
    must be one of them. The original keys are kept.
    """
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as err:
        raise AnswerError(f"{path} is not readable JSON: {err}") from err
    if not isinstance(data, dict):
        raise AnswerError(f"{path} must hold a JSON object, got {type(data).__name__}")
    by = data.get("by")
    if not isinstance(by, str) or not by.strip():
        raise AnswerError('missing field "by": who answered, e.g. "by": "Oleg"')
    decision = decision_of(data)
    if decision is None:
        if "approved" in data:
            raise AnswerError(f'field "approved" must be true or false, got {data["approved"]!r}')
        raise AnswerError('missing field "decision"')
    accepted = [a.get("decision") for a in answers or []]
    if accepted and decision not in accepted:
        raise AnswerError(f'unknown decision {decision!r} in field "decision"; one of {accepted}')
    return {**data, "decision": decision}


def _osa(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def notify(
    run_dir,
    step: str,
    gate: Gate | None,
    ticket: dict,
    app: dict,
    *,
    runner=subprocess.run,
    post=urllib.request.urlopen,
    which=shutil.which,
    platform: str = sys.platform,
) -> list[str]:
    """Tell that a run waits: a macOS notification, and a POST to `notify_url` when one is set.

    Both are best effort: nothing raises; the problems come back as lines for the caller to print.
    """
    gate = gate or Gate(who="", question="", kind="")
    run_dir = Path(run_dir)
    ticket_id = (ticket or {}).get("id") or run_dir.name
    problems = []
    if platform == "darwin" and which("osascript"):
        script = (
            f"display notification {_osa(gate.question[:NOTIFY_CHARS])} "
            f"with title {_osa(f'qa-factory: {ticket_id} waits at {step}')}"
        )
        try:
            runner(["osascript", "-e", script], check=False, capture_output=True, timeout=10)
        except Exception as err:
            problems.append(f"notification: {type(err).__name__}: {err}")
    url = (ticket or {}).get("notify_url") or (app or {}).get("notify_url")
    if url:
        payload = {
            "ticket": ticket_id,
            "step": step,
            "kind": gate.kind,
            "who": gate.who,
            "question": gate.question,
            "run_dir": str(run_dir),
            "question_path": str(run_dir / "question.md"),
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            response = post(request, timeout=POST_TIMEOUT_S)
            if hasattr(response, "close"):
                response.close()
        except Exception as err:
            problems.append(f"POST {url}: {type(err).__name__}: {err}")
    return problems


def last_record(run_dir, step: str) -> StepRecord | None:
    """The step's latest record, `steps/NN-<step>.json`, or None when there is none or it is unreadable.

    A step resuming at its own gate reads it: the driver writes the new record only after the step
    returns, so during the step this is still the record that asked the question.
    """
    for path in sorted((Path(run_dir) / "steps").glob(f"[0-9][0-9]-{step}.json")):
        try:
            return StepRecord.from_dict(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None
    return None


def _latest_records(steps_dir: Path) -> list[Path]:
    """`NN-<step>.json` only: `.roundN` and `.answerN` files are history."""
    return sorted(p for p in steps_dir.glob("[0-9][0-9]-*.json") if "." not in p.stem)


def waiting(runs_root) -> list[dict]:
    """Every run under the root whose latest record of a step waits for a person."""
    root = Path(runs_root)
    found = []
    for run in sorted(p for p in root.iterdir() if (p / "steps").is_dir()) if root.is_dir() else []:
        try:
            ticket_id = json.loads((run / "ticket.json").read_text()).get("id") or run.name
        except (OSError, json.JSONDecodeError):
            ticket_id = run.name
        for path in _latest_records(run / "steps"):
            try:
                rec = StepRecord.from_dict(json.loads(path.read_text()))
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if rec.status != "needs_person":
                continue
            gate = rec.output.gate
            question = gate.question if gate else rec.output.reason
            found.append(
                {
                    "ticket": ticket_id,
                    "step": rec.step,
                    "kind": gate.kind if gate else "-",
                    "who": gate.who if gate else "-",
                    "since": rec.finished,
                    "question": " ".join(str(question).split())[:QUESTION_CHARS],
                    "question_path": str(run / "question.md"),
                    "run_dir": str(run),
                    "answer_pending": (run / "answer.json").exists(),
                }
            )
    return found


def main(runs_root: str = ".artifacts/runs", as_json: bool = False, out: TextIO | None = None) -> int:
    """`python -m factory waiting`: one line per run that waits for a person."""
    out = out or sys.stdout
    root = Path(runs_root)
    if not root.is_absolute():
        from factory.driver import repo_root

        root = repo_root() / root
    rows = waiting(root)
    if as_json:
        out.write(json.dumps(rows, indent=2) + "\n")
        return 0
    if not rows:
        out.write("nothing is waiting\n")
        return 0
    for r in rows:
        pending = "  answer pending" if r["answer_pending"] else ""
        out.write(
            f"{r['ticket']}  {r['step']}  {r['kind']}  who {r['who']}  since {r['since']}  "
            f"{r['question']}  {r['question_path']}{pending}\n"
        )
    return 0
