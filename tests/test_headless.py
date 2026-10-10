"""Tests for the headless Claude Code runner. No real calls: the runner is injected."""

import json
import subprocess
from pathlib import Path

from factory import headless

FIXTURES = Path(__file__).parent / "fixtures"
PLAIN = (FIXTURES / "headless_plain.json").read_text()
SCHEMA_RESULT = (FIXTURES / "headless_schema.json").read_text()


class FakeRunner:
    """Stands in for subprocess.run and records how it was called."""

    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr
        self.argv = None
        self.kwargs = None
        self.settings_text = None

    def __call__(self, argv, **kwargs):
        self.argv, self.kwargs = argv, kwargs
        if "--settings" in argv:
            self.settings_text = Path(argv[argv.index("--settings") + 1]).read_text()
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, self.stderr)


def do_call(runner, **kw):
    args = dict(
        prompt="hi", cwd=".", model="m", budget_usd=0.5, tools="Read", allowed_tools="Read", runner=runner
    )
    args.update(kw)
    return headless.call(**args)


def test_argv_has_required_flags_in_order():
    runner = FakeRunner(PLAIN)
    do_call(runner, tools="", allowed_tools="")
    argv = runner.argv
    assert argv[:3] == ["claude", "-p", "hi"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.50"
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert argv[argv.index("--tools") + 1] == ""
    assert "--no-session-persistence" in argv
    assert "--json-schema" not in argv and "--settings" not in argv and "--add-dir" not in argv


def test_schema_is_stripped_of_dollar_keys():
    runner = FakeRunner(SCHEMA_RESULT)
    schema = {"$schema": "x", "$id": "y", "type": "object", "properties": {}}
    do_call(runner, schema=schema)
    sent = json.loads(runner.argv[runner.argv.index("--json-schema") + 1])
    assert sent == {"type": "object", "properties": {}}


def test_settings_file_is_written_and_removed():
    runner = FakeRunner(PLAIN)
    do_call(runner, settings={"hooks": {}})
    assert json.loads(runner.settings_text) == {"hooks": {}}
    assert not Path(runner.argv[runner.argv.index("--settings") + 1]).exists()


def test_add_dir_is_repeated():
    runner = FakeRunner(PLAIN)
    do_call(runner, add_dirs=["/a", "/b"])
    pairs = [runner.argv[i + 1] for i, a in enumerate(runner.argv) if a == "--add-dir"]
    assert pairs == ["/a", "/b"]


def test_env_is_scrubbed_and_stdin_closed(monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    monkeypatch.setenv("KEEP_ME", "yes")
    runner = FakeRunner(PLAIN)
    do_call(runner, cwd="/work")
    env = runner.kwargs["env"]
    assert "CLAUDECODE" not in env and "CLAUDE_CODE_ENTRYPOINT" not in env
    assert env["KEEP_ME"] == "yes"
    assert runner.kwargs["stdin"] == subprocess.DEVNULL
    assert runner.kwargs["cwd"] == "/work"


def test_parses_real_plain_result():
    res = do_call(FakeRunner(PLAIN))
    raw = json.loads(PLAIN)
    assert res.text == "pong"
    assert res.structured is None
    assert res.is_error is False
    assert res.cost_usd == raw["total_cost_usd"] == 0.017373
    assert res.model == "claude-sonnet-5-5"
    assert res.turns == 1
    assert res.session_id == raw["session_id"]
    assert res.output_tokens == 4
    assert res.metrics() == {
        "cost_usd": 0.017373,
        "model": "claude-sonnet-5-5",
        "turns": 1,
        "duration_ms": raw["duration_ms"],
        "input_tokens": 2,
        "output_tokens": 4,
    }


def test_parses_real_structured_result():
    res = do_call(FakeRunner(SCHEMA_RESULT))
    assert res.structured == {"word": "pong"}
    assert res.cost_usd == 0.0055402
    assert res.turns == 2


def test_structured_falls_back_to_result_text():
    raw = {"result": '{"a": 1}', "is_error": False}
    assert do_call(FakeRunner(json.dumps(raw))).structured == {"a": 1}


def test_error_result_is_flagged():
    raw = {"is_error": True, "subtype": "error_max_budget_usd", "total_cost_usd": 0.1, "errors": ["x"]}
    res = do_call(FakeRunner(json.dumps(raw), returncode=1, stderr="e" * 3000))
    assert res.is_error is True
    assert res.returncode == 1
    assert res.cost_usd == 0.1
    assert len(res.stderr) == 2000
    assert res.model == "m"


def test_unparseable_output_is_an_error():
    res = do_call(FakeRunner("not json at all"))
    assert res.is_error is True
    assert res.raw == {}


def test_noisy_stdout_uses_last_json_line():
    noisy = (
        "warning: something\n" + json.dumps({"result": "old"}) + "\n" + json.dumps(json.loads(PLAIN)) + "\n"
    )
    res = do_call(FakeRunner(noisy))
    assert res.text == "pong"


def test_timeout_is_an_error():
    def runner(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, 1)

    res = do_call(runner, timeout_s=1)
    assert res.is_error and "timed out" in res.stderr


STREAM = "\n".join(
    [
        json.dumps({"type": "system", "subtype": "init"}),
        json.dumps({"type": "assistant", "message": {"content": []}}),
        json.dumps({"type": "result", "result": "streamed", "total_cost_usd": 0.02, "num_turns": 3}),
    ]
)


def test_transcript_uses_stream_json_and_is_saved(tmp_path):
    runner = FakeRunner(STREAM)
    path = tmp_path / "deep" / "transcript.jsonl"
    res = do_call(runner, transcript_path=path)
    argv = runner.argv
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in argv and "json" not in argv
    assert path.read_text() == STREAM
    assert res.text == "streamed" and res.turns == 3 and res.cost_usd == 0.02 and not res.is_error


def test_no_transcript_keeps_json_format():
    runner = FakeRunner(PLAIN)
    do_call(runner)
    assert runner.argv[runner.argv.index("--output-format") + 1] == "json"
    assert "--verbose" not in runner.argv
