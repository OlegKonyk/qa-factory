"""Run Claude Code non-interactively, one fresh session per call.

Checked against `claude --help` for version 2.1.295: every flag used below exists
(-p, --output-format, --model, --max-budget-usd, --permission-mode, --tools,
--allowedTools, --no-session-persistence, --json-schema, --settings, --add-dir).
No difference from the spec. `--tools ""` is accepted ("" disables all tools).

Smoke results (real calls, 2026-10-08, measured):
- Result JSON keys: type, subtype, is_error, result, structured_output (only with --json-schema),
  num_turns, duration_ms, duration_api_ms, total_cost_usd, usage, modelUsage (keyed by model id),
  permission_denials, session_id, stop_reason, terminal_reason, errors (on failure), uuid, and more.
- With a schema the value is in "structured_output"; "result" holds the same JSON as text.
- usage.input_tokens counts only uncached input; cached tokens are in the cache_* fields.
- A cold call costs about 0.10 USD because the system prompt is written to the cache (25k tokens);
  a warm call costs about 0.02 USD or less. A 0.05 budget failed cold (is_error, subtype
  error_max_budget_usd, exit code 1) and passed warm. Use budgets of 0.50 or more.
- The spec says a call from inside a Claude Code session is refused unless CLAUDECODE* variables are
  removed. Not reproduced: a call with those variables present also worked here. The scrub is kept
  because it is harmless.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from factory import blind

PROMPTS_DIR = Path(__file__).parent / "prompts"
FACTORY_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Result:
    """What one headless call returned."""

    text: str = ""
    structured: Any = None
    cost_usd: float = 0.0
    model: str = ""
    turns: int = 0
    duration_ms: int = 0
    session_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    is_error: bool = False
    permission_denials: list = field(default_factory=list)
    returncode: int = 0
    stderr: str = ""
    raw: dict = field(default_factory=dict)

    def metrics(self) -> dict:
        return {
            "cost_usd": self.cost_usd,
            "model": self.model,
            "turns": self.turns,
            "duration_ms": self.duration_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


def clean_env(env: dict | None = None) -> dict:
    """A copy of the environment without the variables that mark a Claude Code session."""
    source = os.environ if env is None else env
    return {k: v for k, v in source.items() if not k.startswith(("CLAUDECODE", "CLAUDE_CODE"))}


def build_argv(
    prompt: str,
    model: str,
    budget_usd: float,
    tools: str,
    allowed_tools: str,
    schema: dict | None = None,
    settings_path: str | None = None,
    add_dirs: Sequence[str] = (),
    binary: str = "claude",
    stream: bool = False,
) -> list[str]:
    argv = [
        binary,
        "-p",
        prompt,
        "--output-format",
        "stream-json" if stream else "json",
        *(["--verbose"] if stream else []),
        "--model",
        model,
        "--max-budget-usd",
        f"{budget_usd:.2f}",
        "--permission-mode",
        "dontAsk",
        "--tools",
        tools,
        "--allowedTools",
        allowed_tools,
        "--no-session-persistence",
    ]
    if schema:
        stripped = {k: v for k, v in schema.items() if k not in ("$schema", "$id")}
        argv += ["--json-schema", json.dumps(stripped)]
    if settings_path:
        argv += ["--settings", settings_path]
    for d in add_dirs:
        argv += ["--add-dir", str(d)]
    return argv


def parse_output(stdout: str) -> dict:
    """The last line of stdout that parses as a JSON object; the whole text is tried first."""
    try:
        whole = json.loads(stdout)
        if isinstance(whole, dict):
            return whole
    except ValueError:
        pass
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return {}


def parse_stream(stdout: str) -> dict:
    """The last stream-json line that is the session's result; else whatever parse_output finds."""
    for line in reversed(stdout.splitlines()):
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "result":
            return obj
    return parse_output(stdout)


def result_from(raw: dict, requested_model: str, returncode: int = 0, stderr: str = "") -> Result:
    text = raw.get("result")
    text = text if isinstance(text, str) else ""
    structured = raw.get("structured_output")
    if structured is None and text:
        try:
            structured = json.loads(text)
        except ValueError:
            structured = None
    usage = raw.get("usage") or {}
    model_usage = raw.get("modelUsage") or {}
    # Several models can appear (a helper model beside the requested one): name the requested one
    # when it is among them, else the one that cost the most.
    if requested_model in model_usage:
        model = requested_model
    elif model_usage:
        model = max(model_usage, key=lambda k: float((model_usage[k] or {}).get("costUSD") or 0.0))
    else:
        model = raw.get("model") or requested_model
    return Result(
        text=text,
        structured=structured,
        cost_usd=float(raw.get("total_cost_usd") or 0.0),
        model=model,
        turns=int(raw.get("num_turns") or 0),
        duration_ms=int(raw.get("duration_ms") or 0),
        session_id=raw.get("session_id") or "",
        input_tokens=int(usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("output_tokens") or 0),
        is_error=bool(raw.get("is_error")) or not raw or returncode != 0,
        permission_denials=list(raw.get("permission_denials") or []),
        returncode=returncode,
        stderr=(stderr or "")[-2000:],
        raw=raw,
    )


def call(
    prompt: str,
    cwd: str | Path,
    model: str,
    budget_usd: float,
    tools: str,
    allowed_tools: str,
    schema: dict | None = None,
    settings: dict | None = None,
    add_dirs: Sequence[str | Path] = (),
    timeout_s: int = 1800,
    binary: str = "claude",
    runner: Callable[..., Any] = subprocess.run,
    transcript_path: str | Path | None = None,
    env: dict | None = None,
) -> Result:
    """One session. `env` is the environment to start it in (default os.environ), scrubbed of the
    Claude Code markers; the test writer passes the application's (`factory/checks/appenv.py`) so
    the tests it runs find the console scripts of the application's environment."""
    settings_file = None
    try:
        if settings:
            fd, settings_file = tempfile.mkstemp(suffix=".json", prefix="qa-factory-settings-")
            with os.fdopen(fd, "w") as f:
                json.dump(settings, f)
        argv = build_argv(
            prompt,
            model,
            budget_usd,
            tools,
            allowed_tools,
            schema,
            settings_file,
            add_dirs,
            binary,
            stream=transcript_path is not None,
        )
        try:
            proc = runner(
                argv,
                cwd=str(cwd),
                env=clean_env(env),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return Result(is_error=True, model=model, returncode=-1, stderr=f"timed out after {timeout_s}s")
        except OSError as err:  # no such binary, or no such working directory
            return Result(
                is_error=True, model=model, returncode=-1, stderr=f"could not start {binary}: {err}"
            )
    finally:
        if settings_file:
            Path(settings_file).unlink(missing_ok=True)
    if transcript_path is not None:
        Path(transcript_path).parent.mkdir(parents=True, exist_ok=True)
        Path(transcript_path).write_text(proc.stdout or "")
        raw = parse_stream(proc.stdout or "")
    else:
        raw = parse_output(proc.stdout or "")
    return result_from(raw, model, proc.returncode, proc.stderr or "")


def _read(path: str | None) -> str:
    return Path(path).read_text() if path and Path(path).is_file() else ""


def one_prompt(
    name: str,
    inp: dict,
    schema: dict,
    model: str,
    budget_usd: float,
    tools: str,
    allowed_tools: str,
    extra: dict | None = None,
    runner: Callable[..., Any] = subprocess.run,
    cwd: str | None = None,
    allow_blind: bool = True,
) -> dict:
    """Fill factory/prompts/<name>.md, make one call, write <run_dir>/<name>/<name>.json."""
    repo = inp["repo"]
    artifacts = inp.get("artifacts") or {}
    is_blind = allow_blind and blind.is_blind(inp["ticket"])
    ticket = blind.public_ticket(inp["ticket"]) if is_blind else inp["ticket"]
    values = {
        "ticket_json": json.dumps(ticket, indent=2),
        "diff": "" if is_blind else _read(artifacts.get("change_diff")),
        "where": blind.WHERE_BLIND if is_blind else blind.WHERE_SEQUENTIAL,
        "strategy": _read(str(FACTORY_ROOT / Path(repo["app"]["strategy"]).expanduser())),
    }
    values.update(extra or {})
    prompt = (PROMPTS_DIR / f"{name}.md").read_text().format_map(values)
    if cwd is None:
        cwd = repo["base_tree"] if is_blind else repo["head_tree"]
    res = call(
        prompt,
        cwd=cwd,
        model=model,
        budget_usd=budget_usd,
        tools=tools,
        allowed_tools=allowed_tools,
        schema=schema,
        settings=blind.settings(blind.hidden_paths(repo, FACTORY_ROOT)) if is_blind else None,
        runner=runner,
    )
    metrics = res.metrics()
    if res.is_error or res.structured is None:
        reason = res.text or res.stderr or "no structured output"
        return {
            "status": "fail",
            "artifacts": {},
            "reason": f"{name} call failed: {reason}",
            "gate": None,
            "metrics": metrics,
        }
    out_dir = Path(inp["run_dir"]) / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.json"
    out.write_text(json.dumps({"structured": res.structured, "text": res.text, "metrics": metrics}, indent=2))
    return {"status": "pass", "artifacts": {name: str(out)}, "reason": "", "gate": None, "metrics": metrics}
