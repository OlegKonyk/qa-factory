"""The Restate workflow's logic, driven by a fake context: steps, the gate, failures, the lock."""

import asyncio
import json
import threading
import time
from datetime import timedelta

import pytest
from restate import TerminalError

from factory import __main__ as cli
from factory import gates, restate_service, stub_steps
from factory.driver import STEP_NAMES
from factory.envelope import Gate


class Parked(Exception):
    """Raised by the fake when the workflow waits on a promise nobody has resolved."""


class FakePromise:
    def __init__(self, ctx, name):
        self.ctx, self.name = ctx, name

    async def value(self):
        if self.name not in self.ctx.promises:
            raise Parked(self.name)
        return self.ctx.promises[self.name]

    async def resolve(self, value):
        self.ctx.promises[self.name] = value


class FakeContext:
    """Just enough of a Restate workflow context: durable steps run at once and are journalled."""

    def __init__(self, key="t-1", promises=None):
        self._key = key
        self.journal: list[str] = []
        self.state: dict = {}
        self.promises: dict = dict(promises or {})

    def key(self):
        return self._key

    async def run_typed(self, name, fn, _options, *args):
        self.journal.append(name)
        return fn(*args)

    def set(self, name, value):
        self.state[name] = value

    async def get(self, name, type_hint=None):
        return self.state.get(name)

    def clear(self, name):
        self.state.pop(name, None)

    def promise(self, name, type_hint=None):
        return FakePromise(self, name)


@pytest.fixture
def ticket(tmp_path):
    app = tmp_path / "app.json"
    app.write_text(json.dumps({"name": "stub", "worktrees": str(tmp_path / "wt")}))

    def make(**extra):
        data = {"id": "t-1", "app": str(app), "base": "a", "head": "b", "title": "stub", **extra}
        path = tmp_path / "ticket.json"
        path.write_text(json.dumps(data))
        return {"ticket": str(path), "runs_root": str(tmp_path / "runs")}

    return make


def drive(ctx, req, steps=None):
    return asyncio.run(restate_service.run_ticket(ctx, req, steps or stub_steps.STEPS))


def test_runs_six_durable_steps_and_writes_the_driver_records(ticket, tmp_path):
    ctx = FakeContext()
    result = drive(ctx, ticket())
    run_dir = tmp_path / "runs" / "t-1"
    assert result == {"status": "pass", "step": None, "reason": "", "run_dir": str(run_dir)}
    assert ctx.journal == [
        "prepare",
        "01-frame",
        "02-plan",
        "03-implement",
        "04-verify",
        "05-review",
        "06-ship",
    ]
    assert sorted(p.name for p in (run_dir / "steps").glob("*.json")) == [
        f"0{i}-{n}.json" for i, n in enumerate(STEP_NAMES, start=1)
    ]
    assert "step" not in ctx.state


def test_a_gate_parks_on_a_promise_and_the_answer_resumes_the_step(ticket, tmp_path):
    req = ticket(gate="person")
    first = FakeContext()
    with pytest.raises(Parked, match="verify-1"):
        drive(first, req)
    assert first.state["gate"] == {
        "promise": "verify-1",
        "step": "verify",
        "question": "Approve the stub tests?",
    }
    run_dir = tmp_path / "runs" / "t-1"
    question = (run_dir / "question.md").read_text()
    assert "/factory/t-1/answer" in question

    # Restate replays the workflow once the promise is resolved; the passed steps are not run again.
    replay = FakeContext(promises={"verify-1": {"approved": True, "by": "Oleg"}})
    result = drive(replay, req)
    assert result["status"] == "pass"
    assert replay.journal[-4:] == ["answer verify-1", "04-verify #2", "05-review", "06-ship"]
    assert (run_dir / "steps" / "04-verify.answer1.json").exists()
    assert not (run_dir / "answer.json").exists()
    starts = [
        line.split()[1] for line in (run_dir / "stub_calls.log").read_text().splitlines() if "start" in line
    ]
    assert starts.count("frame") == 1 and starts.count("verify") == 2
    assert (run_dir / "question.md").read_text().count("Under Restate") == 1


def hinted_answer(hint: str) -> dict:
    """The JSON the hint's curl command sends."""
    return json.loads(hint.split("-d '", 1)[1].rsplit("'", 1)[0])


def test_the_answer_hint_sends_the_gates_first_accepted_answer_and_who(tmp_path):
    answers = [{"decision": "sign_off"}, {"decision": "another_round"}, {"decision": "decline"}]
    gate = Gate(who="Dana", question="Sign off?", kind="review", answers=answers)
    hint = restate_service.answer_hint("t-1", gate)
    assert "/factory/t-1/answer" in hint
    sent = hinted_answer(hint)
    assert sent == {"decision": "sign_off", "by": "Dana", "note": ""}
    path = tmp_path / "answer.json"
    path.write_text(json.dumps(sent))
    assert gates.read_answer(path, answers)["decision"] == "sign_off"  # the driver would take it


def test_the_answer_hint_without_accepted_answers_says_approve():
    sent = hinted_answer(restate_service.answer_hint("t-1", Gate(who="", question="q")))
    assert sent == {"decision": "approve", "by": "Oleg", "note": ""}
    assert hinted_answer(restate_service.answer_hint("t-1"))["decision"] == "approve"


def test_a_declined_answer_fails_the_run_at_that_step(ticket):
    result = drive(
        FakeContext(promises={"verify-1": {"approved": False, "by": "Oleg", "note": "no"}}),
        ticket(gate="person"),
    )
    assert result["status"] == "fail"
    assert result["step"] == "verify"
    assert "declined: no" in result["reason"]


def test_a_failing_step_ends_the_workflow_without_running_later_steps(ticket):
    calls = []

    def failing(step_input):
        calls.append("plan")
        return {"status": "fail", "reason": "plan broke"}

    steps = {**stub_steps.STEPS, "plan": failing}
    ctx = FakeContext()
    result = drive(ctx, ticket(), steps)
    assert (result["status"], result["step"], result["reason"]) == ("fail", "plan", "plan broke")
    assert ctx.journal[-1] == "02-plan"


def test_a_step_that_raises_becomes_a_fail_output_not_a_restate_retry(ticket):
    def boom(step_input):
        raise RuntimeError("bug in a step")

    result = drive(FakeContext(), ticket(), {**stub_steps.STEPS, "frame": boom})
    assert result["status"] == "fail"
    assert "RuntimeError: bug in a step" in result["reason"]


def test_answer_resolves_the_open_gate_and_refuses_when_none_is_open():
    ctx = FakeContext()
    with pytest.raises(TerminalError):
        asyncio.run(restate_service.answer_gate(ctx, {"approved": True}))
    ctx.state["gate"] = {"promise": "verify-2", "step": "verify", "question": "?"}
    out = asyncio.run(restate_service.answer_gate(ctx, {"approved": True}))
    assert out == {"resolved": "verify-2", "step": "verify"}
    assert ctx.promises["verify-2"] == {"approved": True}


def test_a_retried_attempt_waits_for_the_running_copy_and_skips_the_step(ticket):
    """Restate retries a step it cut off while the old attempt's thread still runs; it must not run twice."""
    req = ticket()
    run = restate_service.prepare(req["ticket"], req["runs_root"])
    calls = []

    def slow(step_input):
        calls.append(time.monotonic())
        time.sleep(0.5)
        return {"status": "pass", "artifacts": {"verify": "x"}}

    steps = {**stub_steps.STEPS, "verify": slow}
    outs = []

    def attempt():
        outs.append(restate_service.step(steps, "t-1", 4, "verify", run, {}))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
        time.sleep(0.1)
    for t in threads:
        t.join()
    assert len(calls) == 1
    assert [o["status"] for o in outs] == ["pass", "pass"]
    assert "skip  4 verify" in outs[1]["log"]


def test_the_workflow_has_three_handlers_and_timeouts_that_fit_a_long_verify():
    wf = restate_service.build(stub_steps.STEPS)
    assert wf.name == "factory"
    assert set(wf.handlers) == {"run", "answer", "status"}
    assert wf.inactivity_timeout >= timedelta(minutes=15)
    assert wf.abort_timeout >= timedelta(minutes=15)
    short = restate_service.build(stub_steps.STEPS, inactivity_s=5, abort_s=7)
    assert (short.inactivity_timeout, short.abort_timeout) == (timedelta(seconds=5), timedelta(seconds=7))


def test_run_with_the_restate_engine_submits_the_ticket(ticket, monkeypatch, capsys):
    sent = []
    monkeypatch.setattr(
        restate_service, "_post", lambda url, body=None: sent.append((url, body)) or {"id": 1}
    )
    req = ticket()
    assert cli.main(["run", req["ticket"], "--engine", "restate", "--runs-root", "r"]) == 0
    url, body = sent[0]
    assert url == f"{restate_service.INGRESS}/factory/t-1/run/send"
    assert body == {"ticket": req["ticket"], "runs_root": "r"}
    assert json.loads(capsys.readouterr().out) == {"key": "t-1", "id": 1}
    cli.main(["run", req["ticket"], "--engine", "restate", "--key", "t-1.2"])
    assert sent[1][0].endswith("/factory/t-1.2/run/send")


def test_until_is_refused_with_the_restate_engine(ticket):
    with pytest.raises(SystemExit):
        cli.main(["run", ticket()["ticket"], "--engine", "restate", "--until", "plan"])


def test_restate_answer_posts_the_answer_file(tmp_path, monkeypatch, capsys):
    sent = []
    monkeypatch.setattr(
        restate_service, "_post", lambda url, body=None: sent.append((url, body)) or {"ok": 1}
    )
    answer = tmp_path / "answer.json"
    answer.write_text('{"approved": true}')
    assert cli.main(["restate", "answer", "t-1", str(answer)]) == 0
    assert sent == [(f"{restate_service.INGRESS}/factory/t-1/answer", {"approved": True})]
