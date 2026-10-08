"""The lint check for generated test files: the application's ruff config plus three checks of our own.

- ruff check and ruff format --check, run with the application's interpreter in its tree, so the
  application's own ruff configuration applies.
- "no-assertion": a test function or method that asserts nothing.
- "sleep": a call to time.sleep, which makes tests slow and timing-dependent.
- "mocks-own-code": unittest.mock.patch of a name inside the application's own package, which
  replaces the code the test is meant to exercise.
"""

import ast
import json
import re
import subprocess
from pathlib import Path

# ruff 0.14 prints "Would reformat: <path>";
# ruff 0.16 prints "unformatted: ..." then " --> <path>:<row>:<col>".
_REFORMAT_OLD = re.compile(r"^Would reformat:\s*(.+)$")
_REFORMAT_NEW = re.compile(r"^-->\s*(.+?):(\d+):\d+$")


def _finding(file, line, rule, message):
    return {"file": file, "line": line, "rule": rule, "message": message}


def _rel(tree, path):
    p = Path(path)
    try:
        return str(p.resolve().relative_to(Path(tree).resolve()))
    except ValueError:
        return str(path)


def _ruff(tree, python, files):
    findings = []
    probe = subprocess.run([python, "-m", "ruff", "--version"], cwd=tree, capture_output=True, text=True)
    if probe.returncode != 0:
        return [
            _finding(None, None, "ruff", f"ruff is not installed for {python}: {probe.stderr.strip()[-200:]}")
        ]
    proc = subprocess.run(
        [python, "-m", "ruff", "check", "--no-cache", "--output-format", "json", *files],
        cwd=tree,
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 1):
        return [_finding(None, None, "ruff", f"ruff check failed: {proc.stderr.strip()[-300:]}")]
    for item in json.loads(proc.stdout or "[]"):
        line = (item.get("location") or {}).get("row")
        findings.append(
            _finding(
                _rel(tree, Path(tree) / item["filename"]), line, item.get("code") or "ruff", item["message"]
            )
        )
    proc = subprocess.run(
        [python, "-m", "ruff", "format", "--check", "--no-cache", *files],
        cwd=tree,
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 1):
        return findings + [_finding(None, None, "ruff", f"ruff format failed: {proc.stderr.strip()[-300:]}")]
    after_header = False
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        old, new = _REFORMAT_OLD.match(line), _REFORMAT_NEW.match(line)
        if old:
            findings.append(
                _finding(_rel(tree, Path(tree) / old.group(1)), None, "format", "ruff would reformat")
            )
        elif new and after_header:
            path = _rel(tree, Path(tree) / new.group(1))
            findings.append(_finding(path, int(new.group(2)), "format", "ruff would reformat"))
        after_header = line.startswith("unformatted:")
    return findings


def _callee(node):
    """The called name: `f` for f(...), `assertEqual` for self.assertEqual(...)."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _asserts(fn):
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = _callee(node)
            if name.startswith("assert") or name == "expect" or _dotted(node.func) == "pytest.raises":
                return True
    return False


def _sleep_names(module):
    """Names bound to time.sleep by `from time import sleep [as x]`."""
    names = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == "time":
            names |= {a.asname or a.name for a in node.names if a.name == "sleep"}
    return names


def _patch_target(call):
    if call.args:
        first = call.args[0]
    else:
        first = next((k.value for k in call.keywords if k.arg == "target"), None)
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _ast_findings(rel, source, app_package):
    try:
        module = ast.parse(source, filename=rel)
    except SyntaxError as e:
        return [_finding(rel, e.lineno, "syntax", f"the file does not parse: {e.msg}")]
    findings, sleeps = [], _sleep_names(module)
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            if not _asserts(node):
                findings.append(_finding(rel, node.lineno, "no-assertion", f"{node.name} asserts nothing"))
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted(node.func)
        if dotted == "time.sleep" or (isinstance(node.func, ast.Name) and node.func.id in sleeps):
            findings.append(
                _finding(rel, node.lineno, "sleep", "time.sleep makes the test slow and timing-dependent")
            )
        if app_package and dotted in ("patch", "mock.patch", "unittest.mock.patch"):
            target = _patch_target(node)
            if target and (target == app_package or target.startswith(app_package + ".")):
                findings.append(
                    _finding(
                        rel,
                        node.lineno,
                        "mocks-own-code",
                        f"patches {target}, part of the application itself",
                    )
                )
    return findings


def _excluded(rel, exclude_dirs):
    parts = Path(rel).parts
    return any(parts[: len(Path(d).parts)] == Path(d).parts for d in exclude_dirs)


def run(tree, python, files, exclude_dirs=(), app_package=None):
    """Lint `files` (paths relative to `tree`). Files under any of `exclude_dirs` are skipped.

    The "mocks-own-code" rule runs only when `app_package` is given.
    """
    rels = [_rel(tree, Path(tree) / f) for f in files]
    rels = [r for r in rels if not _excluded(r, exclude_dirs)]
    if not rels:
        return {"status": "pass", "findings": []}
    findings = _ruff(tree, python, rels)
    for rel in rels:
        findings += _ast_findings(rel, (Path(tree) / rel).read_text(encoding="utf-8"), app_package)
    return {"status": "pass" if not findings else "fail", "findings": findings}
