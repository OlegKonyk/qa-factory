"""The gate contract: modes per step, the answer file, telling a person, and the waiting list."""

import io
import json
from pathlib import Path

import pytest

from factory import __main__ as cli
from factory import gates
from factory.envelope import Gate

APPROVAL = [{"decision": "approve", "means": "join"}, {"decision": "decline", "means": "fail"}]


# mode_for


def test_mode_defaults_verify_model_and_every_other_step_auto():
    assert gates.mode_for("verify", {}, {}) == "model"
    assert [gates.mode_for(s, {}, {}) for s in ("frame", "plan", "review", "ship")] == ["auto"] * 4


def test_mode_ticket_wins_over_recipe_wins_over_default():
    recipe = {"gates": {"verify": "auto", "plan": "person"}}
    assert gates.mode_for("verify", {"gates": {"verify": "person"}}, recipe) == "person"
    assert gates.mode_for("verify", {}, recipe) == "auto"
    assert gates.mode_for("plan", {"gates": {"verify": "person"}}, recipe) == "person"
    assert gates.mode_for("plan", {"gates": {"plan": "auto"}}, recipe) == "auto"


def test_the_legacy_gate_field_means_verify_person():
    assert gates.mode_for("verify", {"gate": "person"}, {}) == "person"
    assert gates.mode_for("verify", {}, {"gate": "person"}) == "person"
    assert gates.mode_for("verify", {"gate": "auto"}, {"gate": "person"}) == "auto"
    assert gates.mode_for("plan", {"gate": "person"}, {}) == "auto"
    # within one file gates.verify wins; the ticket's legacy field wins over the recipe's gates
    assert gates.mode_for("verify", {"gate": "person", "gates": {"verify": "auto"}}, {}) == "auto"
    assert gates.mode_for("verify", {"gate": "person"}, {"gates": {"verify": "auto"}}) == "person"


def test_an_unknown_mode_is_refused():
    with pytest.raises(ValueError, match="ticket gates.verify"):
        gates.mode_for("verify", {"gates": {"verify": "always"}}, {})


# read_answer


def _answer(tmp_path, data) -> Path:
    path = tmp_path / "answer.json"
    path.write_text(json.dumps(data))
    return path


def test_an_answer_without_by_is_refused(tmp_path):
    with pytest.raises(gates.AnswerError, match='missing field "by"'):
        gates.read_answer(_answer(tmp_path, {"decision": "approve", "note": "fine"}), APPROVAL)
    with pytest.raises(gates.AnswerError, match='missing field "by"'):
        gates.read_answer(_answer(tmp_path, {"approved": True, "by": " "}))


def test_an_unknown_decision_is_refused_and_named(tmp_path):
    with pytest.raises(gates.AnswerError, match="unknown decision 'maybe'"):
        gates.read_answer(_answer(tmp_path, {"decision": "maybe", "by": "Oleg"}), APPROVAL)


def test_a_missing_decision_and_a_bad_file_are_refused(tmp_path):
    with pytest.raises(gates.AnswerError, match='missing field "decision"'):
        gates.read_answer(_answer(tmp_path, {"by": "Oleg"}))
    with pytest.raises(gates.AnswerError, match='"approved" must be true or false'):
        gates.read_answer(_answer(tmp_path, {"approved": "yes", "by": "Oleg"}))
    (tmp_path / "bad.json").write_text("{not json")
    with pytest.raises(gates.AnswerError, match="not readable JSON"):
        gates.read_answer(tmp_path / "bad.json")


def test_approved_maps_to_a_decision_and_keeps_the_original_keys(tmp_path):
    yes = gates.read_answer(_answer(tmp_path, {"approved": True, "by": "Oleg", "note": "ok"}), APPROVAL)
    assert yes == {"approved": True, "by": "Oleg", "note": "ok", "decision": "approve"}
    no = gates.read_answer(_answer(tmp_path, {"approved": False, "by": "Oleg"}), APPROVAL)
    assert no["decision"] == "decline"


def test_without_accepted_answers_any_decision_is_read(tmp_path):
    assert gates.read_answer(_answer(tmp_path, {"decision": "stop", "by": "Oleg"}))["decision"] == "stop"


# notify

GATE = Gate(who="Oleg", question='Approve "these" tests?' + "x" * 300, kind="approval", answers=APPROVAL)


class Recorder:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.fail:
            raise OSError("boom")


def test_notify_shows_one_notification_and_posts_one_payload(tmp_path):
    runner, post = Recorder(), Recorder()
    problems = gates.notify(
        tmp_path / "t-1",
        "verify",
        GATE,
        {"id": "t-1", "notify_url": "http://hook.test/x"},
        {},
        runner=runner,
        post=post,
        which=lambda name: "/usr/bin/osascript",
        platform="darwin",
    )
    assert problems == []
    assert len(runner.calls) == 1 and len(post.calls) == 1
    argv = runner.calls[0][0][0]
    assert argv[:2] == ["osascript", "-e"]
    assert 'with title "qa-factory: t-1 waits at verify"' in argv[2]
    assert '\\"these\\"' in argv[2] and "x" * 200 not in argv[2]
    request, kwargs = post.calls[0][0][0], post.calls[0][1]
    assert kwargs == {"timeout": 5}
    assert request.get_method() == "POST" and request.full_url == "http://hook.test/x"
    assert json.loads(request.data) == {
        "ticket": "t-1",
        "step": "verify",
        "kind": "approval",
        "who": "Oleg",
        "question": GATE.question,
        "run_dir": str(tmp_path / "t-1"),
        "question_path": str(tmp_path / "t-1" / "question.md"),
    }


def test_notify_raises_nothing_when_both_fail(tmp_path):
    problems = gates.notify(
        tmp_path,
        "verify",
        GATE,
        {"id": "t-1"},
        {"notify_url": "http://hook.test/x"},
        runner=Recorder(fail=True),
        post=Recorder(fail=True),
        which=lambda name: "/usr/bin/osascript",
        platform="darwin",
    )
    assert len(problems) == 2
    assert problems[0].startswith("notification: OSError") and problems[1].startswith(
        "POST http://hook.test/x"
    )


def test_notify_does_nothing_off_macos_and_without_a_url(tmp_path):
    runner, post = Recorder(), Recorder()
    gates.notify(tmp_path, "verify", GATE, {"id": "t-1"}, {}, runner=runner, post=post, platform="linux")
    gates.notify(
        tmp_path, "verify", GATE, {}, {}, runner=runner, post=post, which=lambda n: None, platform="darwin"
    )
    assert runner.calls == [] and post.calls == []


# waiting


def _record(
    step: str, index: int, status: str, gate: dict | None = None, finished="2026-10-14T10:00:00+00:00"
):
    return {
        "step": step,
        "index": index,
        "status": status,
        "input": {"ticket": {}, "repo": {}, "artifacts": {}, "round": 1, "run_dir": "/x"},
        "output": {"status": status, "artifacts": {}, "reason": "why", "gate": gate, "metrics": {}},
        "started": finished,
        "finished": finished,
        "duration_s": 1.0,
    }


def _run(root: Path, name: str, files: dict) -> Path:
    run = root / name
    (run / "steps").mkdir(parents=True)
    (run / "ticket.json").write_text(json.dumps({"id": name}))
    for rel, data in files.items():
        (run / rel).write_text(json.dumps(data))
    return run


ASK = {
    "who": "Oleg",
    "question": "Approve?\n" + "q" * 200,
    "context": {},
    "kind": "approval",
    "answers": APPROVAL,
}


@pytest.fixture
def runs(tmp_path):
    root = tmp_path / "runs"
    _run(root, "a-waiting", {"steps/04-verify.json": _record("verify", 4, "needs_person", ASK)})
    _run(
        root,
        "b-pending",
        {
            "steps/04-verify.json": _record("verify", 4, "needs_person", ASK),
            "answer.json": {"decision": "approve", "by": "Oleg"},
        },
    )
    _run(root, "c-finished", {"steps/06-ship.json": _record("ship", 6, "pass")})
    _run(
        root,
        "d-history",
        {
            "steps/04-verify.round1.json": _record("verify", 4, "needs_person", ASK),
            "steps/04-verify.answer1.json": {"decision": "approve", "by": "Oleg"},
            "steps/04-verify.json": _record("verify", 4, "pass"),
        },
    )
    (root / "not-a-run").mkdir()
    return root


def test_waiting_lists_the_waiting_run_and_the_pending_answer_only(runs):
    found = gates.waiting(runs)
    assert [(r["ticket"], r["step"], r["answer_pending"]) for r in found] == [
        ("a-waiting", "verify", False),
        ("b-pending", "verify", True),
    ]
    first = found[0]
    assert first["kind"] == "approval" and first["who"] == "Oleg"
    assert first["since"] == "2026-10-14T10:00:00+00:00"
    assert first["question"] == ("Approve? " + "q" * 200)[:100]
    assert first["question_path"] == str(runs / "a-waiting" / "question.md")


def test_waiting_command_prints_one_line_each_and_json(runs, capsys):
    assert cli.main(["waiting", "--runs-root", str(runs)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith(
        "a-waiting  verify  approval  who Oleg  since 2026-10-14T10:00:00+00:00  Approve? "
    )
    assert lines[0].endswith(str(runs / "a-waiting" / "question.md"))
    assert lines[1].endswith("answer pending")
    assert cli.main(["waiting", "--runs-root", str(runs), "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2


def test_nothing_waiting(tmp_path):
    out = io.StringIO()
    assert gates.main(str(tmp_path), out=out) == 0
    assert out.getvalue() == "nothing is waiting\n"
