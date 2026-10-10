"""Tests for the blind-mode helpers and for Frame running blind. No real calls."""

import json
from pathlib import Path

import pytest

from factory import blind
from factory.steps import frame
from tests.test_headless import FakeRunner

TICKET = {
    "id": "t-1",
    "title": "A ticket",
    "description": "Does a thing",
    "acceptance_criteria": ["a"],
    "base": "BASECOMMIT",
    "head": "HEADCOMMIT",
    "source": "SOURCEPR",
    "app": "targets/x/app.json",
    "caps": {"rounds": 2},
    "gate": "plan",
    "qa_mode": "blind",
}


@pytest.fixture
def layout(tmp_path):
    wt = tmp_path / "wt"
    for tree in ("t-1/base", "t-1/head", "t-0/base", "t-0/head"):
        (wt / tree).mkdir(parents=True)
    clone = tmp_path / "clone"
    clone.mkdir()
    root = tmp_path / "factory"
    root.mkdir()
    repo = {
        "app": {"repo": str(clone), "worktrees": str(wt), "strategy": str(root / "strategy.md")},
        "base_tree": str(wt / "t-1" / "base"),
        "head_tree": str(wt / "t-1" / "head"),
    }
    (root / "strategy.md").write_text("STRATEGY")
    return repo, root


def test_is_blind():
    assert blind.is_blind(TICKET)
    assert not blind.is_blind({"id": "x"})
    assert not blind.is_blind({"qa_mode": "sequential"})


def test_public_ticket_drops_exactly_the_hidden_fields():
    public = blind.public_ticket(TICKET)
    assert set(TICKET) - set(public) == set(blind.HIDDEN_FIELDS)
    assert public["title"] == "A ticket" and public["acceptance_criteria"] == ["a"]
    assert public["description"] == "Does a thing"


def test_hidden_paths_lists_everything_but_the_base_tree(layout):
    repo, root = layout
    paths = blind.hidden_paths(repo, root)
    resolved = lambda p: str(Path(p).resolve())  # noqa: E731
    wt = Path(repo["app"]["worktrees"])
    expected = {
        resolved(repo["app"]["repo"]),
        resolved(wt / "t-1" / "head"),
        resolved(wt / "t-0" / "base"),
        resolved(wt / "t-0" / "head"),
        resolved(root),
    }
    assert set(paths) == expected
    assert paths == sorted(set(paths))
    assert resolved(repo["base_tree"]) not in paths


def test_settings_deny_with_double_slash_and_keep_base():
    base = {"permissions": {"deny": ["Read(//old/**)"]}, "hooks": {}}
    out = blind.settings(["/a/b"], base)
    deny = out["permissions"]["deny"]
    assert deny[0] == "Read(//old/**)"
    assert "Read(//a/b/**)" in deny and "Write(//a/b/**)" in deny and "Glob(//a/b/**)" in deny
    assert "Bash(git *)" in deny and "Bash(git)" in deny
    assert out["hooks"] == {} and base["permissions"]["deny"] == ["Read(//old/**)"]
    assert len(deny) == len(set(deny))
    assert blind.settings(["/a/b"], out) == out


def write_transcript(path, calls):
    lines = ["not json"]
    for name, tool_input in calls:
        item = {"type": "tool_use", "name": name, "input": tool_input}
        lines.append(json.dumps({"type": "assistant", "message": {"content": [item]}}))
    lines.append(json.dumps({"type": "user", "message": {"content": []}}))
    lines.append(json.dumps({"type": "result"}))
    path.write_text("\n".join(lines))


def test_audit_flags_hidden_reads_and_git(tmp_path):
    path = tmp_path / "t.jsonl"
    write_transcript(
        path,
        [
            ("Read", {"file_path": "/hidden/x/app.py"}),
            ("Bash", {"command": "git log"}),
            ("Bash", {"command": "  cd /base && git diff"}),
            ("Bash", {"command": "ls gitignore-notes"}),
            ("Read", {"file_path": "/base/app.py"}),
        ],
    )
    report = blind.audit(path, ["/hidden/x"])
    assert report["tool_calls"] == 5 and not report["clean"]
    assert [f["tool"] for f in report["flagged"]] == ["Read", "Bash", "Bash"]
    assert report["transcript"] == str(path)


def test_audit_clean_and_missing(tmp_path):
    path = tmp_path / "t.jsonl"
    write_transcript(path, [("Read", {"file_path": "/base/app.py"})])
    assert blind.audit(path, ["/hidden"]) == {
        "tool_calls": 1,
        "flagged": [],
        "clean": True,
        "transcript": str(path),
    }
    missing = blind.audit(tmp_path / "none.jsonl", ["/hidden"])
    assert missing["error"] == "no transcript" and missing["clean"] is False and missing["tool_calls"] == 0


def frame_input(layout, tmp_path, ticket):
    repo, _ = layout
    repo = dict(repo, base="BASECOMMIT", head="HEADCOMMIT")
    diff = tmp_path / "change.diff"
    diff.write_text("+ SECRET DIFF")
    return {
        "ticket": ticket,
        "repo": repo,
        "artifacts": {"change_diff": str(diff)},
        "round": 1,
        "run_dir": str(tmp_path / "run"),
    }


RESULT = json.dumps(
    {
        "result": "ok",
        "structured_output": {"acceptance_criteria": [], "ambiguities": [], "summary": "s"},
        "total_cost_usd": 0.01,
    }
)


def test_frame_blind_uses_base_tree_settings_and_public_ticket(layout, tmp_path):
    inp = frame_input(layout, tmp_path, TICKET)
    runner = FakeRunner(RESULT)
    out = frame.run(inp, runner=runner)
    assert out["status"] == "pass"
    assert runner.kwargs["cwd"] == inp["repo"]["base_tree"]
    deny = json.loads(runner.settings_text)["permissions"]["deny"]
    head = str(Path(inp["repo"]["head_tree"]).resolve())
    assert f"Read(/{head}/**)" in deny and "Bash(git *)" in deny
    prompt = runner.argv[2]
    assert blind.WHERE_BLIND in prompt and blind.WHERE_SEQUENTIAL not in prompt
    assert "A ticket" in prompt and "SECRET DIFF" not in prompt
    for hidden in ("BASECOMMIT", "HEADCOMMIT", "SOURCEPR", "qa_mode", '"base"', '"head"', '"source"'):
        assert hidden not in prompt


def test_frame_sequential_uses_head_tree_and_full_ticket(layout, tmp_path):
    ticket = dict(TICKET, qa_mode="sequential")
    inp = frame_input(layout, tmp_path, ticket)
    runner = FakeRunner(RESULT)
    frame.run(inp, runner=runner)
    assert runner.kwargs["cwd"] == inp["repo"]["head_tree"]
    assert "--settings" not in runner.argv
    prompt = runner.argv[2]
    assert blind.WHERE_SEQUENTIAL in prompt and "HEADCOMMIT" in prompt and "SECRET DIFF" in prompt


def test_allow_blind_false_and_cwd_override(layout, tmp_path):
    from factory.headless import one_prompt

    inp = frame_input(layout, tmp_path, TICKET)
    runner = FakeRunner(RESULT)
    one_prompt("frame", inp, frame.SCHEMA, "m", 0.5, "Read", "Read", runner=runner, allow_blind=False)
    assert runner.kwargs["cwd"] == inp["repo"]["head_tree"] and "--settings" not in runner.argv
    assert "HEADCOMMIT" in runner.argv[2]
    one_prompt("frame", inp, frame.SCHEMA, "m", 0.5, "Read", "Read", runner=runner, cwd="/elsewhere")
    assert runner.kwargs["cwd"] == "/elsewhere"


def test_review_prompt_without_where_still_fills():
    text = (Path(blind.__file__).parent / "prompts" / "review.md").read_text()
    assert "{where}" not in text
    assert (
        text.format_map({"where": "x", "ticket_json": "", "strategy": "", "test_files": "", "diff": ""})
        is not None
    )


def test_audit_lets_the_application_interpreter_run_but_not_read_beside_it(tmp_path):
    python = "/hidden/clone/.venv/bin/python"
    path = tmp_path / "t.jsonl"
    write_transcript(
        path,
        [
            ("Bash", {"command": f"{python} -m pytest -p no:cacheprovider bookmarks/tests/test_x_api.py"}),
            ("Bash", {"command": f"{python} -m ruff check bookmarks/tests/test_x_api.py"}),
            ("Bash", {"command": f"{python} -c 'open(\"/hidden/clone/bookmarks/queries.py\")'"}),
        ],
    )
    report = blind.audit(path, ["/hidden/clone"], allowed=[python])
    assert report["tool_calls"] == 3
    assert len(report["flagged"]) == 1 and "queries.py" in report["flagged"][0]["input"]
