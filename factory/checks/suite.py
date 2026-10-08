"""Run the application's own test suite against a source tree and report what happened."""

import re
import subprocess
import time

_SUMMARY = re.compile(r"\d+ (passed|failed|error)")


def run(tree, python, invocations, pytest_args, timeout=1800) -> dict:
    """Run pytest once per invocation inside `tree` and collect the outcome of each run.

    Status is "pass" only when every run exits with code 0.
    """
    runs = []
    for invocation in invocations:
        args = [str(python), "-m", "pytest", *pytest_args, *invocation]
        start = time.monotonic()
        try:
            proc = subprocess.run(
                args,
                cwd=tree,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            returncode, output = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired as exc:
            returncode = -1
            raw = (exc.stdout or b"") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            output = (raw.decode(errors="replace") if isinstance(raw, bytes) else raw) + "\ntimed out"
        lines = output.splitlines()
        summary = next((line for line in reversed(lines) if _SUMMARY.search(line)), "")
        runs.append(
            {
                "args": args,
                "returncode": returncode,
                "summary": summary,
                "wall_s": round(time.monotonic() - start, 2),
                "tail": lines[-20:],
            }
        )
    status = "pass" if all(r["returncode"] == 0 for r in runs) else "fail"
    return {"status": status, "runs": runs}
