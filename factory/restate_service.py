"""The factory as a Restate workflow: one workflow per ticket, each step a durable step.

Behind a flag; the plain driver stays the default. Each step runs `driver.run_step` inside
`ctx.run`, so the run folder gets the same records as under the plain driver, and Restate's journal
holds every finished step: after a crash the workflow replays and only the step in flight runs
again. A step that needs a person parks the workflow on a durable promise, resolved by an HTTP call
to the workflow's `answer` handler.

    python -m factory restate serve [--port 9080] [--steps factory.stub_steps]
    python -m factory restate register
    python -m factory run <ticket.json> --engine restate [--key <workflow key>]
    python -m factory restate answer <key> <answer.json>
"""

from __future__ import annotations

import fcntl
import importlib
import io
import json
import os
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path

import restate
from restate import RunOptions, TerminalError, Workflow, WorkflowContext, WorkflowSharedContext

from factory import driver
from factory.driver import STEP_NAMES, StepFn

WORKFLOW = "factory"
# A Verify of about 15 minutes runs as one step, and Restate hears nothing from the service while it
# runs. Restate asks for a suspension after the inactivity timeout and cuts the step off after the
# abort timeout that follows, then retries the step from its start. Both are raised well past a
# Verify; the environment overrides them, so a test can measure the cut-off with seconds.
INACTIVITY_S = float(os.environ.get("FACTORY_RESTATE_INACTIVITY_S", 30 * 60))
ABORT_S = float(os.environ.get("FACTORY_RESTATE_ABORT_S", 30 * 60))
INGRESS = os.environ.get("RESTATE_INGRESS", "http://localhost:8080")
ADMIN = os.environ.get("RESTATE_ADMIN", "http://localhost:9070")


def load_steps(module: str | None = None) -> dict[str, StepFn]:
    """The real steps, or `STEPS` of the named module (the stub steps, for a run with no model calls)."""
    if module is None:
        return driver.load_steps()
    return dict(importlib.import_module(module).STEPS)


def prepare(ticket_path: str, runs_root: str) -> dict:
    """The ticket, its repository trees and its run folder, as one JSON-ready dict."""
    ticket, repo, run_dir = driver.prepare(ticket_path, runs_root)
    return {"ticket": ticket, "repo": repo, "run_dir": str(run_dir)}


def answer_hint(key: str) -> str:
    return (
        f"\nUnder Restate, answer over HTTP instead of writing the file:\n\n"
        f"    curl -X POST {INGRESS}/{WORKFLOW}/{key}/answer -H 'content-type: application/json' "
        f'-d \'{{"approved": true, "by": "Oleg", "note": ""}}\'\n'
    )


def step(steps: dict[str, StepFn], key: str, index: int, name: str, run: dict, artifacts: dict) -> dict:
    """One durable step: `driver.run_step` on the run folder; its output as a dict.

    When Restate cuts off an attempt that outlived its timeouts, the step's thread keeps running and
    Restate starts the step again. The lock makes the new attempt wait for the old one and then find
    its record, so a step never runs twice at once in the same worktree.
    """
    log = io.StringIO()
    run_dir = Path(run["run_dir"])
    with (run_dir / "steps" / f"{index:02d}-{name}.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        output = driver.run_step(
            index, name, steps[name], run["ticket"], run["repo"], run_dir, artifacts, log
        )
    question = run_dir / "question.md"
    if output.status == "needs_person" and question.exists():
        hint = answer_hint(key)
        if hint not in question.read_text():
            with question.open("a") as f:
                f.write(hint)
    print(log.getvalue(), end="", flush=True)
    return {**output.to_dict(), "log": log.getvalue()}


def write_answer(run_dir: str, answer: dict) -> str:
    """Put a person's answer where the step reads it, as the plain driver's answer file."""
    path = Path(run_dir) / "answer.json"
    path.write_text(json.dumps(answer, indent=2) + "\n")
    return str(path)


async def run_ticket(ctx, req: dict, steps: dict[str, StepFn]) -> dict:
    """The workflow body, kept apart from the SDK's decorators so a fake context can drive it."""
    key = ctx.key()
    once = RunOptions(max_attempts=3)
    run = await ctx.run_typed(
        "prepare", prepare, once, req["ticket"], req.get("runs_root", ".artifacts/runs")
    )
    artifacts: dict[str, str] = {}
    for index, name in enumerate(STEP_NAMES, start=1):
        attempt = 1
        while True:
            ctx.set("step", {"index": index, "name": name, "attempt": attempt})
            label = f"{index:02d}-{name}" + (f" #{attempt}" if attempt > 1 else "")
            out = await ctx.run_typed(label, step, once, steps, key, index, name, run, artifacts)
            if out["status"] != "needs_person":
                break
            gate = f"{name}-{attempt}"
            question = (out.get("gate") or {}).get("question") or out.get("reason", "")
            ctx.set("gate", {"promise": gate, "step": name, "question": question})
            answer = await ctx.promise(gate, type_hint=dict).value()
            ctx.clear("gate")
            await ctx.run_typed(f"answer {gate}", write_answer, once, run["run_dir"], answer)
            attempt += 1
        if out["status"] == "fail":
            ctx.clear("step")
            return {"status": "fail", "step": name, "reason": out["reason"], "run_dir": run["run_dir"]}
        artifacts.update(out["artifacts"])
    ctx.clear("step")
    return {"status": "pass", "step": None, "reason": "", "run_dir": run["run_dir"]}


async def answer_gate(ctx, answer: dict) -> dict:
    """Resolve the promise of the gate the workflow waits on; 409 when it waits on none."""
    gate = await ctx.get("gate", type_hint=dict)
    if not gate:
        raise TerminalError("this run is not waiting for a person", 409)
    await ctx.promise(gate["promise"], type_hint=dict).resolve(answer)
    return {"resolved": gate["promise"], "step": gate["step"]}


def build(steps: dict[str, StepFn], inactivity_s: float = INACTIVITY_S, abort_s: float = ABORT_S):
    """The Restate workflow over the given step functions."""
    wf = Workflow(
        WORKFLOW,
        description="One ticket through frame, plan, implement, verify, review and ship.",
        inactivity_timeout=timedelta(seconds=inactivity_s),
        abort_timeout=timedelta(seconds=abort_s),
    )

    @wf.main(name="run")
    async def run(ctx: WorkflowContext, req: dict) -> dict:
        return await run_ticket(ctx, req, steps)

    @wf.handler(name="answer")
    async def answer(ctx: WorkflowSharedContext, req: dict) -> dict:
        return await answer_gate(ctx, req)

    @wf.handler(name="status")
    async def status(ctx: WorkflowSharedContext) -> dict:
        return {"step": await ctx.get("step", type_hint=dict), "gate": await ctx.get("gate", type_hint=dict)}

    return wf


def serve(port: int = 9080, steps_module: str | None = None) -> int:
    """Serve the workflow over HTTP/2 for the Restate server to call."""
    import asyncio

    from hypercorn.asyncio import serve as hypercorn_serve
    from hypercorn.config import Config

    app = restate.app(services=[build(load_steps(steps_module))])
    config = Config()
    config.bind = [f"127.0.0.1:{port}"]
    print(
        f"factory workflow on :{port} (steps: {steps_module or 'factory.steps'}, "
        f"inactivity {INACTIVITY_S:g} s, abort {ABORT_S:g} s)",
        flush=True,
    )
    asyncio.run(hypercorn_serve(app, config))
    return 0


def _post(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body if body is not None else {}).encode()
    request = urllib.request.Request(url, data=data, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode()
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"{url}: HTTP {err.code}: {err.read().decode()[:300]}") from err
    return json.loads(text) if text.strip() else {}


def register(uri: str = "http://127.0.0.1:9080") -> dict:
    """Tell the Restate server where the service listens (again after a change: force)."""
    return _post(f"{ADMIN}/deployments", {"uri": uri, "force": True})


def submit(ticket_path: str, key: str | None = None, runs_root: str = ".artifacts/runs") -> dict:
    """Start the ticket's workflow without waiting; the key defaults to the ticket id."""
    ticket = json.loads(Path(ticket_path).read_text())
    key = key or ticket["id"]
    req = {"ticket": str(Path(ticket_path).resolve()), "runs_root": runs_root}
    return {"key": key, **_post(f"{INGRESS}/{WORKFLOW}/{key}/run/send", req)}


def answer(key: str, answer_path: str) -> dict:
    """Resolve the gate a run waits on with a person's answer file."""
    return _post(f"{INGRESS}/{WORKFLOW}/{key}/answer", json.loads(Path(answer_path).read_text()))
