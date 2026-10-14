"""The data every step receives and returns, and the record the driver keeps of each run of a step."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

STATUSES = ("pass", "fail", "needs_person")


def now_iso() -> str:
    """Current time as an ISO-8601 string in UTC."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _check_status(status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")


@dataclass
class Gate:
    """A question for a person: who should answer, what is asked, and the facts they need.

    `kind` names the gate in one word (`approval`, `escalation`, ...). `answers` lists the accepted
    answers, each `{"decision": "<word>", "means": "<one sentence>", "carries": "<optional field>"}`;
    an empty list (every record written before gates had one) accepts any decision.
    """

    who: str
    question: str
    context: dict = field(default_factory=dict)
    kind: str = "approval"
    answers: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Gate:
        return cls(
            who=data["who"],
            question=data["question"],
            context=data.get("context") or {},
            kind=data.get("kind") or "approval",
            answers=list(data.get("answers") or []),
        )


@dataclass
class StepInput:
    """What a step is given: the ticket, the repository trees, earlier artifacts and the round."""

    ticket: dict
    repo: dict
    artifacts: dict
    round: int
    run_dir: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StepInput:
        return cls(
            ticket=data["ticket"],
            repo=data["repo"],
            artifacts=dict(data.get("artifacts") or {}),
            round=data["round"],
            run_dir=data["run_dir"],
        )


@dataclass
class StepOutput:
    """What a step returns: a status, the files it made, why, and an optional question."""

    status: str
    artifacts: dict = field(default_factory=dict)
    reason: str = ""
    gate: Gate | None = None
    metrics: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _check_status(self.status)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["gate"] = self.gate.to_dict() if self.gate else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> StepOutput:
        gate = data.get("gate")
        return cls(
            status=data["status"],
            artifacts=dict(data.get("artifacts") or {}),
            reason=data.get("reason", ""),
            gate=Gate.from_dict(gate) if gate else None,
            metrics=dict(data.get("metrics") or {}),
        )


@dataclass
class StepRecord:
    """One run of one step, as written to steps/NN-<name>.json."""

    step: str
    index: int
    status: str
    input: StepInput
    output: StepOutput
    started: str
    finished: str
    duration_s: float

    def __post_init__(self) -> None:
        _check_status(self.status)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["input"] = self.input.to_dict()
        data["output"] = self.output.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> StepRecord:
        return cls(
            step=data["step"],
            index=data["index"],
            status=data["status"],
            input=StepInput.from_dict(data["input"]),
            output=StepOutput.from_dict(data["output"]),
            started=data["started"],
            finished=data["finished"],
            duration_s=data["duration_s"],
        )
