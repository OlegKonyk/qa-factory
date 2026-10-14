"""The workflow on a real Restate server: kill the service mid-step, park at the gate, answer over HTTP.

Needs `restate-server` (the `RESTATE_SERVER` variable, or on PATH); skipped without it. Stub steps
only: no model calls, no application.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from factory import restate_service

ROOT = Path(__file__).resolve().parent.parent
SERVER = os.environ.get("RESTATE_SERVER") or shutil.which("restate-server")

pytestmark = [
    pytest.mark.restate,
    pytest.mark.skipif(not SERVER, reason="restate-server not found (set RESTATE_SERVER or put it on PATH)"),
]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for(check, timeout=60.0, every=0.2):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = check()
        if value:
            return value
        time.sleep(every)
    raise AssertionError(f"timed out after {timeout} s")


def listening(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def http(method: str, url: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {} if body is None else {"content-type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode()
    except OSError:
        return None, ""


@pytest.fixture
def restate(tmp_path, monkeypatch):
    ingress, admin, node, service = (free_port() for _ in range(4))
    env = {
        **os.environ,
        "RESTATE_INGRESS__BIND_ADDRESS": f"127.0.0.1:{ingress}",
        "RESTATE_ADMIN__BIND_ADDRESS": f"127.0.0.1:{admin}",
        "RESTATE_BIND_ADDRESS": f"127.0.0.1:{node}",
        "RESTATE_ADVERTISED_ADDRESS": f"http://127.0.0.1:{node}",
        "RESTATE_DEFAULT_RETRY_POLICY__MAX_INTERVAL": "1s",
    }
    server = subprocess.Popen(
        [SERVER, "--base-dir", str(tmp_path / "data"), "--no-logo", "--listen-mode", "tcp"],
        env=env,
        stdout=(tmp_path / "server.log").open("w"),
        stderr=subprocess.STDOUT,
    )
    monkeypatch.setattr(restate_service, "INGRESS", f"http://127.0.0.1:{ingress}")
    monkeypatch.setattr(restate_service, "ADMIN", f"http://127.0.0.1:{admin}")
    procs = []

    def start_service():
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "factory",
                "restate",
                "serve",
                "--port",
                str(service),
                "--steps",
                "factory.stub_steps",
            ],
            cwd=ROOT,
            env={**os.environ, "QA_FACTORY_NO_NOTIFY": "1"},  # no desktop notification from a test
            stdout=(tmp_path / "service.log").open("a"),
            stderr=subprocess.STDOUT,
        )
        procs.append(proc)
        wait_for(lambda: listening(service))
        return proc

    try:
        wait_for(lambda: http("GET", f"http://127.0.0.1:{admin}/health")[0] == 200)
        start_service()
        restate_service.register(f"http://127.0.0.1:{service}")
        yield {"ingress": f"http://127.0.0.1:{ingress}", "start_service": start_service, "procs": procs}
    finally:
        for proc in [*procs, server]:
            proc.kill()
            proc.wait()


def test_kill_mid_step_resumes_from_the_journal_and_the_gate_is_answered_over_http(restate, tmp_path):
    app = tmp_path / "app.json"
    app.write_text(json.dumps({"name": "stub", "worktrees": str(tmp_path / "wt")}))
    ticket = tmp_path / "ticket.json"
    ticket.write_text(
        json.dumps(
            {
                "id": "live-1",
                "app": str(app),
                "base": "a",
                "head": "b",
                "title": "live",
                "gate": "person",
                "stub": {"sleep_s": {"verify": 3}},
            }
        )
    )
    log = tmp_path / "runs" / "live-1" / "stub_calls.log"
    ingress = restate["ingress"]

    restate_service.submit(str(ticket), runs_root=str(tmp_path / "runs"))
    wait_for(lambda: log.exists() and "verify start" in log.read_text())
    restate["procs"][-1].send_signal(signal.SIGKILL)
    restate["procs"][-1].wait()
    restate["start_service"]()

    gate = wait_for(
        lambda: json.loads(http("POST", f"{ingress}/factory/live-1/status")[1] or "{}").get("gate")
    )
    assert gate["promise"] == "verify-1"
    status, body = http("POST", f"{ingress}/factory/live-1/answer", {"approved": True, "by": "test"})
    assert status == 200, body
    status, body = http("GET", f"{ingress}/restate/workflow/factory/live-1/attach")
    assert status == 200, body
    assert json.loads(body)["status"] == "pass"

    starts = [line.split()[1] for line in log.read_text().splitlines() if line.split()[2] == "start"]
    # Frame, Plan and Implement ran once: the restarted service replayed them from the journal.
    # Verify ran three times: cut off by the kill, again until it asked, and once more with the answer.
    assert starts == ["frame", "plan", "implement", "verify", "verify", "verify", "review", "ship"]
    status, body = http("POST", f"{ingress}/factory/live-1/answer", {"approved": True})
    assert status == 409
