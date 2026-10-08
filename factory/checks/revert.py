"""The revert check: a new test must pass with the change and fail for a behaviour reason without it.

Each new test file runs twice with the failure-recording pytest plugin (failsort_plugin.py): once in
the tree at the change (head), once in a copy of that tree whose changed source files are put back
as they were before the change (base) while the tests stay as at head. Every failure in the copy is
sorted into a cause: an assertion that fails (the test checks behaviour), a name the test needs that
does not exist before the change (the test only proves the code is new), or anything else (a crash).
"""

import fnmatch
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

CAUSES = ("pass", "skip", "missing-name", "behaviour", "crash")
PLUGIN = "factory.checks.failsort_plugin"
FACTORY_ROOT = Path(__file__).resolve().parents[2]
OFFENDING = ("head-fails", "missing-name", "crash")


def _short(name):
    return name.rsplit(".", 1)[-1]


def _path_ends_with(file, suffix):
    file, suffix = file.replace(os.sep, "/"), str(suffix).replace(os.sep, "/").removeprefix("./")
    return file == suffix or file.endswith("/" + suffix)


def _missing_name(names, message):
    if names & {"ImportError", "ModuleNotFoundError"}:
        return True
    if "NameError" in names and "UnboundLocalError" not in names:
        return True
    if "AttributeError" in names and "has no attribute" in message:
        return True
    if "TypeError" in names and (
        "unexpected keyword argument" in message or ("missing" in message and "required" in message)
    ):
        return True
    return "NoReverseMatch" in names


def classify(record, test_file, support_paths):
    """Sort one plugin record into one of CAUSES."""
    outcome = record.get("outcome")
    if outcome == "passed":
        return "pass"
    if outcome == "skipped":
        return "skip"
    mro = record.get("exc_mro") or ([record["exc_type"]] if record.get("exc_type") else [])
    names = {_short(n) for n in mro}
    message = record.get("message") or ""
    owned = [p for p in (test_file, *support_paths) if p]
    frames = record.get("frames") or []
    if any(n.endswith("AssertionError") for n in names) and any(
        _path_ends_with(f.get("file", ""), p) for f in frames for p in owned
    ):
        return "behaviour"
    if _missing_name(names, message) or record.get("kind") == "collect":
        return "missing-name"
    return "crash"


def _env(out):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(FACTORY_ROOT), env.get("PYTHONPATH")) if p)
    env["QA_FACTORY_FAILSORT_OUT"] = str(out)
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # leave the application's tree as it was
    return env


def _read(out):
    records, done = {}, False
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("event") == "done":
                done = True
            elif obj.get("nodeid") is not None:
                records[obj["nodeid"]] = obj
    return records, done


def _run_tree(tree, label, files, workdir, counter, python, pytest_args, support, browser_glob, timeout):
    """Run each test file in `tree`. Returns ({nodeid: (cause, record)}, seconds, error or None)."""
    results, start = {}, time.monotonic()
    for test_file in files:
        counter[0] += 1
        out = Path(workdir) / f"{counter[0]}.jsonl"
        out.unlink(missing_ok=True)
        cmd = [python, "-m", "pytest", *pytest_args, "-p", PLUGIN]
        if browser_glob and fnmatch.fnmatch(Path(test_file).name, browser_glob):
            cmd += ["-o", f"python_files={browser_glob}"]
        cmd.append(str(test_file))
        try:
            proc = subprocess.run(
                cmd, cwd=tree, env=_env(out), capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return (
                results,
                time.monotonic() - start,
                f"pytest timed out after {timeout}s on {test_file} {label}",
            )
        records, done = _read(out)
        if not done:
            tail = " ".join((proc.stderr or proc.stdout or "").strip().splitlines()[-3:])
            return (
                results,
                time.monotonic() - start,
                (f"pytest on {test_file} {label} ended without a result (exit {proc.returncode}): {tail}"),
            )
        for nodeid, rec in records.items():
            results[nodeid] = (classify(rec, str(test_file), support), rec)
    return results, time.monotonic() - start, None


def _build_reverted(head_tree, base_tree, changed_source, target, exclude_copy):
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(head_tree, target, symlinks=True, ignore=shutil.ignore_patterns(*exclude_copy))
    for entry in changed_source:
        path, status = entry["path"], entry["status"]
        dest = target / path
        if status == "A":
            dest.unlink(missing_ok=True)
        elif status in ("M", "D"):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(base_tree) / path, dest)
        else:
            raise ValueError(f"unknown change status {status!r} for {path}")


def _reverted_result(nodeid, reverted):
    """The test's own record, or the collection failure of the file or class that holds it."""
    if nodeid in reverted:
        return reverted[nodeid]
    holders = [
        k for k, (_, rec) in reverted.items() if rec.get("kind") == "collect" and nodeid.startswith(k + "::")
    ]
    if holders:
        return reverted[max(holders, key=len)]
    return "crash", {"message": "the test gave no result in the reverted tree"}


def _verdict(at_head, reverted):
    if at_head != "pass":
        return "head-fails"
    return {"behaviour": "proves-behaviour", "pass": "passes-without-change"}.get(reverted, reverted)


def run(
    head_tree,
    base_tree,
    changed_source,
    new_test_files,
    workdir,
    python,
    pytest_args,
    test_support,
    browser_glob,
    exclude_copy,
    timeout=900,
):
    """Run the revert check. `timeout` applies to each pytest invocation, in seconds."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    target = workdir / "reverted"
    report = {
        "status": "fail",
        "reason": "",
        "tests": {},
        "wall_s": {"head": 0.0, "reverted": 0.0},
        "reverted_tree": str(target),
    }
    counter, support = [0], list(test_support)
    common = (new_test_files, workdir, counter, python, pytest_args, support, browser_glob, timeout)

    head, secs, err = _run_tree(head_tree, "at head", *common)
    report["wall_s"]["head"] = round(secs, 2)
    if err:
        report["reason"] = err
        return report

    _build_reverted(Path(head_tree), base_tree, changed_source, target, exclude_copy)
    reverted, secs, err = _run_tree(target, "with the change reverted", *common)
    report["wall_s"]["reverted"] = round(secs, 2)
    if err:
        report["reason"] = err
        return report

    for nodeid, (at_head, head_rec) in head.items():
        rev_cause, rev_rec = _reverted_result(nodeid, reverted)
        verdict = _verdict(at_head, rev_cause)
        message = head_rec.get("message") if verdict == "head-fails" else rev_rec.get("message")
        report["tests"][nodeid] = {
            "at_head": at_head,
            "reverted": rev_cause,
            "verdict": verdict,
            "message": message or "",
        }

    offenders = [(i, t["verdict"]) for i, t in report["tests"].items() if t["verdict"] in OFFENDING]
    proving = [i for i, t in report["tests"].items() if t["verdict"] == "proves-behaviour"]
    if offenders:
        report["reason"] = "; ".join(f"{v}: {i}" for i, v in offenders)
    elif not proving:
        report["reason"] = "no test fails on an assertion when the change is reverted"
    else:
        report["status"] = "pass"
        report["reason"] = (
            f"{len(proving)} of {len(report['tests'])} tests fail on an assertion without the change"
        )
    return report
