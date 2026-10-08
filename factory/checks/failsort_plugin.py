"""A pytest plugin that records, per test, how it ended and where an exception came from.

Loaded with `-p factory.checks.failsort_plugin` (PYTHONPATH carries the factory's repository root).
It appends one JSON object per line to the file named by the environment variable
QA_FACTORY_FAILSORT_OUT, and does nothing when that variable is unset.

One line per test, or per file (or class) that failed to collect:
    nodeid      pytest node id
    kind        "test", or "collect" for a node that failed or was skipped at collection
    outcome     passed | failed | error | skipped   (error: setup or teardown failed)
    phase       setup | call | teardown | collect   (the phase that decided the outcome)
    exc_type    qualified class name: "AttributeError", "json.decoder.JSONDecodeError", ...
    exc_mro     the class and its bases, same naming, without object
    message     str(exception), first 300 characters
    frames      the whole traceback, outermost first, unfiltered: [{"file", "line", "function"}]
and a final line {"event": "done", "exitstatus": N}.

Starts from the old lab's failure sorter, without its request capture and stream protocol.
Standard library and pytest only, so it runs in the application's own interpreter.
"""

import json
import os
import re
import traceback

MSG_LEN = 300
OUT_ENV = "QA_FACTORY_FAILSORT_OUT"

_records = {}
_written = set()
_E_LINE = re.compile(r"^E\s+([A-Za-z_][\w.]*):\s?(.*)$")


def _emit(obj):
    path = os.environ.get(OUT_ENV)
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def type_name(cls):
    mod = getattr(cls, "__module__", "") or ""
    name = getattr(cls, "__qualname__", None) or cls.__name__
    return name if mod == "builtins" else f"{mod}.{name}"


def _message(exc):
    try:
        return str(exc)[:MSG_LEN]
    except Exception as e:  # a broken __str__ still gives a record
        return f"<str() raised {type(e).__name__}>"


def _unwrap(exc):
    """pytest wraps an import error at collection in a CollectError raised `from` it."""
    for _ in range(5):
        if type(exc).__name__ == "CollectError" and exc.__cause__ is not None:
            exc = exc.__cause__
        else:
            break
    return exc


def describe(exc, tb):
    real = _unwrap(exc)
    if real is not exc:
        tb = real.__traceback__
    return {
        "exc_type": type_name(type(real)),
        "exc_mro": [type_name(c) for c in type(real).__mro__ if c is not object],
        "message": _message(real),
        "frames": [
            {"file": f.filename, "line": f.lineno, "function": f.name} for f in traceback.extract_tb(tb)
        ],
    }


def _from_text(rec, longrepr):
    """Fallback when no exception object was seen: the last 'E   Type: message' line."""
    text = str(longrepr or "")
    exc_type, message = None, (text.strip().splitlines() or [""])[-1][:MSG_LEN]
    for line in text.splitlines():
        m = _E_LINE.match(line)
        if m:
            exc_type, message = m.group(1), m.group(2)[:MSG_LEN]
    rec.update(exc_type=exc_type, exc_mro=[exc_type] if exc_type else [], message=message)


def _blank(nodeid, kind):
    return dict(
        nodeid=nodeid, kind=kind, outcome=None, phase=None, exc_type=None, exc_mro=[], message="", frames=[]
    )


def _skip_reason(report):
    lr = report.longrepr
    reason = lr[2] if isinstance(lr, tuple) and len(lr) == 3 else lr
    return str(getattr(report, "wasxfail", "") or reason or "")[:MSG_LEN]


def pytest_exception_interact(node, call, report):
    """Called with the real exception for a failing setup, call, teardown or collection."""
    if call.excinfo is None:
        return
    kind = "collect" if report.when == "collect" else "test"
    rec = _records.setdefault(report.nodeid, _blank(report.nodeid, kind))
    # pytest logs the report before calling this hook, so a record may hold only the text fallback
    # (no frames); the real exception replaces it. After that, the first exception decides.
    if not rec["frames"]:
        rec.update(describe(call.excinfo.value, call.excinfo.tb))


def pytest_runtest_logreport(report):
    """A failure beats a skip, which beats a pass. Setup and teardown failures are errors."""
    rec = _records.setdefault(report.nodeid, _blank(report.nodeid, "test"))
    if rec["outcome"] in ("failed", "error"):
        return
    if report.failed:
        rec["outcome"] = "failed" if report.when == "call" else "error"
        rec["phase"] = report.when
        if rec["exc_type"] is None:
            _from_text(rec, report.longrepr)
    elif report.skipped:
        rec.update(outcome="skipped", phase=report.when, message=_skip_reason(report))
    elif report.when == "call" and rec["outcome"] is None:
        rec.update(outcome="passed", phase="call")


def pytest_runtest_logfinish(nodeid, location):
    rec = _records.get(nodeid)
    if rec is not None and nodeid not in _written:
        _written.add(nodeid)
        _emit(rec)


def pytest_collectreport(report):
    if not (report.failed or report.skipped):
        return
    rec = _records.setdefault(report.nodeid, _blank(report.nodeid, "collect"))
    rec["phase"] = "collect"
    if report.failed:
        rec["outcome"] = "error"
        if rec["exc_type"] is None:
            _from_text(rec, report.longrepr)
    else:
        rec.update(outcome="skipped", message=_skip_reason(report))
    if report.nodeid not in _written:
        _written.add(report.nodeid)
        _emit(rec)


def pytest_sessionfinish(session, exitstatus):
    try:
        status = int(exitstatus)
    except (TypeError, ValueError):
        status = None
    _emit({"event": "done", "exitstatus": status})
