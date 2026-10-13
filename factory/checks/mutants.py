"""Mutation testing (mutmut) limited to the functions a change touched.

Facts measured on linkding at commit 0490013 with mutmut 3.8.0:
- Config lives in `[tool.mutmut]` of pyproject.toml: source_paths, only_mutate,
  pytest_add_cli_args_test_selection, pytest_add_cli_args and use_git_change_detection = false.
  Without `-o django_find_project=false` pytest-django puts the original tree ahead of the mutated
  copy on sys.path and mutmut reports "could not find any test case for any mutant".
- The mutated copy lives in `mutants/`. The app's settings resolve the data dir relative to the copy,
  so `mutants/data/assets`, `favicons` and `previews` must exist before `mutmut run`.
- `mutmut run '<module>.<mangled>__mutmut_*'` limits the run to those mutants. A top-level function
  `f` is mangled `x_f`; a method `m` of class `C` is `xǁCǁm` (the bars are U+01C1).
- Results are in `mutants/<relpath>.meta` (the `.py` stays in the name): JSON with
  `exit_code_by_key`. Codes 1 or 3 mean killed, 0 survived, 5 or 33 no tests,
  36/-24/24/152/255 timeout, null not checked, anything else other.
- Scoped run on one function with the developers' test_queries.py: 454 generated, 108 checked,
  98 killed, 10 survived, 115 s wall (measured).
- The mutated module holds `def x_<f>__mutmut_orig(...)` and one `def x_<f>__mutmut_N(...)` per
  mutant, same signature, usually one line differs.
"""

import ast
import difflib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

BAR = "ǁ"

KILLED = {1, 3}
SURVIVED = {0}
NO_TESTS = {5, 33}
TIMEOUT = {36, -24, 24, 152, 255}


def _functions(src: str) -> dict[str, ast.AST]:
    """Top-level functions and methods of top-level classes, keyed by qualified name."""
    found: dict[str, ast.AST] = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    found[f"{node.name}.{item.name}"] = item
    return found


def changed_functions(base_src: str | None, head_src: str, module: str) -> list[str]:
    """mutmut globs for functions that are new or whose code differs between base and head."""
    base = _functions(base_src) if base_src else {}
    globs = []
    for qualified, node in _functions(head_src).items():
        old = base.get(qualified)
        if old is not None and ast.dump(old, include_attributes=False) == ast.dump(
            node, include_attributes=False
        ):
            continue
        if "." in qualified:
            cls, name = qualified.split(".", 1)
            globs.append(f"{module}.x{BAR}{cls}{BAR}{name}__mutmut_*")
        else:
            globs.append(f"{module}.x_{qualified}__mutmut_*")
    return globs


def changed_lines(base_src: str | None, head_src: str) -> set[int]:
    """1-based head line numbers that were replaced or inserted relative to base."""
    base_lines = (base_src or "").splitlines()
    head_lines = head_src.splitlines()
    matcher = difflib.SequenceMatcher(None, base_lines, head_lines, autojunk=False)
    lines: set[int] = set()
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            lines.update(range(j1 + 1, j2 + 1))
    return lines


def function_def_line(head_src: str, qualified_name: str) -> int | None:
    """Line number of the `def` of a function ("f" or "Class.f") in the head source."""
    node = _functions(head_src).get(qualified_name)
    return node.lineno if node is not None else None


def _defs_anywhere(src: str):
    """Every function definition in a module, class bodies included (mutmut keeps a method's
    mutants inside its class)."""
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node


def _function_lines(src: str, name: str) -> list[str] | None:
    lines = src.splitlines()
    for node in _defs_anywhere(src):
        if node.name == name:
            return lines[node.lineno - 1 : node.end_lineno]
    return None


def mutant_lines(mutated_module_src: str, func_mangled: str) -> dict[str, int | None]:
    """For each mutant of one function, the offset from the `def` line of the first changed line.

    The def line is offset 0, so a change on the first body line is offset 1. None means the mutant
    is identical to the original.
    """
    orig = _function_lines(mutated_module_src, f"{func_mangled}__mutmut_orig")
    result: dict[str, int | None] = {}
    if orig is None:
        return result
    for node in _defs_anywhere(mutated_module_src):
        prefix = f"{func_mangled}__mutmut_"
        if not node.name.startswith(prefix) or node.name == f"{prefix}orig":
            continue
        mutant = _function_lines(mutated_module_src, node.name) or []
        result[node.name] = _first_difference(orig, mutant)
    return result


def _first_difference(orig: list[str], mutant: list[str]) -> int | None:
    # The def line differs only by name, so comparison starts after it.
    a, b = orig[1:], mutant[1:]
    if a == b:
        return None
    if len(a) == len(b):
        return next(i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y) + 1
    for tag, i1, _i2, _j1, _j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            return i1 + 1
    return None


NOTHING_MATCHES = "Filtered for specific mutants, but nothing matches"


def classify_exit(timed_out, returncode, found_meta, output, timeout) -> tuple[str, str, bool]:
    """(status, reason, no_mutants) for one mutmut run.

    mutmut 3.8.0 makes no mutant for some function shapes (measured on isso 7e91d59: a decorator and
    the two functions it decorates got none); asked for those by name it aborts with NOTHING_MATCHES
    and exit code 1. That is not a failure of the tests, so it is reported as "no mutants" and the
    caller skips the mutation verdict instead of sending the writer into a repair round.
    """
    if timed_out:
        return "fail", f"mutmut did not finish within {timeout} seconds", False
    if returncode != 0 and NOTHING_MATCHES in output:
        return "pass", "mutmut made no mutant for any changed function (it skips some shapes)", True
    if returncode != 0 and not found_meta:
        return "fail", f"mutmut exited with code {returncode} and wrote no results", False
    return "pass", "mutmut ran", False


def status_of(code) -> str:
    if code is None:
        return "not_checked"
    if code in KILLED:
        return "killed"
    if code in SURVIVED:
        return "survived"
    if code in NO_TESTS:
        return "no_tests"
    if code in TIMEOUT:
        return "timeout"
    return "other"


def _score(killed: int, survived: int) -> float | None:
    return killed / (killed + survived) if killed + survived else None


def summarize_meta(meta: dict) -> dict:
    """Count mutants by outcome from a parsed `.meta` file."""
    counts = {
        "generated": 0,
        "checked": 0,
        "killed": 0,
        "survived": 0,
        "no_tests": 0,
        "timeout": 0,
        "other": 0,
    }
    for code in meta.get("exit_code_by_key", {}).values():
        counts["generated"] += 1
        status = status_of(code)
        if status == "not_checked":
            continue
        counts["checked"] += 1
        counts[status] += 1
    counts["score"] = _score(counts["killed"], counts["survived"])
    return counts


def _toml_list(items) -> str:
    return "[" + ", ".join(json.dumps(str(i)) for i in items) + "]"


def _mutmut_config(only_mutate, test_files, pytest_add_cli_args, source_package) -> str:
    return (
        "\n[tool.mutmut]\n"
        f"source_paths = {_toml_list([source_package])}\n"
        f"only_mutate = {_toml_list(only_mutate)}\n"
        f"pytest_add_cli_args_test_selection = {_toml_list(test_files)}\n"
        f"pytest_add_cli_args = {_toml_list(pytest_add_cli_args)}\n"
        "use_git_change_detection = false\n"
    )


def _symbol_of(mutant_key: str) -> tuple[str, str]:
    """From a full mutant key return (mangled function name, qualified name)."""
    name = mutant_key.rsplit(".", 1)[-1]
    mangled = name.rsplit("__mutmut_", 1)[0]
    if mangled.startswith(f"x{BAR}"):
        _, cls, meth = mangled.split(BAR, 2)
        return mangled, f"{cls}.{meth}"
    return mangled, mangled[2:] if mangled.startswith("x_") else mangled


def run(
    head_tree,
    python,
    source_package,
    only_mutate,
    test_files,
    globs,
    workdir,
    pytest_add_cli_args,
    pre_create_dirs,
    exclude_copy,
    changed_lines_by_file,
    timeout=1800,
) -> dict:
    """Copy the head tree, run mutmut on the chosen mutants and report kills and survivors."""
    tree = Path(workdir) / "mutation"
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(head_tree, tree, ignore=shutil.ignore_patterns(*exclude_copy))
    pyproject = tree / "pyproject.toml"
    existing = pyproject.read_text() if pyproject.exists() else ""
    pyproject.write_text(
        existing + _mutmut_config(only_mutate, test_files, pytest_add_cli_args, source_package)
    )
    for d in pre_create_dirs:
        (tree / "mutants" / d).mkdir(parents=True, exist_ok=True)

    mutmut = os.path.join(os.path.dirname(str(python)), "mutmut")
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            [mutmut, "run", *globs],
            cwd=tree,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        returncode, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        timed_out, returncode, output = True, None, "mutmut timed out"
    wall_s = round(time.monotonic() - start, 2)

    mutants: dict[str, dict] = {}
    all_codes: dict = {}
    found_meta = False
    for relpath in only_mutate:
        meta_path = tree / "mutants" / f"{relpath}.meta"
        if not meta_path.exists():
            continue
        found_meta = True
        meta = json.loads(meta_path.read_text())
        codes = meta.get("exit_code_by_key", {})
        all_codes.update(codes)
        head_src = (tree / relpath).read_text()
        mutated_src = (tree / "mutants" / relpath).read_text()
        lines_changed = changed_lines_by_file.get(relpath, set())
        offsets: dict[str, int | None] = {}
        seen: set[str] = set()
        for key, code in codes.items():
            status = status_of(code)
            if status == "not_checked":
                continue
            mangled, qualified = _symbol_of(key)
            if mangled not in seen:
                seen.add(mangled)
                offsets.update(mutant_lines(mutated_src, mangled))
            offset = offsets.get(key.rsplit(".", 1)[-1])
            def_line = function_def_line(head_src, qualified)
            line = def_line + offset if def_line is not None and offset is not None else None
            mutants[key] = {"status": status, "line": line, "changed_line": line in lines_changed}

    counts = summarize_meta({"exit_code_by_key": all_codes})
    on_changed = [m for m in mutants.values() if m["changed_line"]]
    ck = sum(m["status"] == "killed" for m in on_changed)
    cs = sum(m["status"] == "survived" for m in on_changed)

    status, reason, no_mutants = classify_exit(timed_out, returncode, found_meta, output, timeout)
    return {
        "status": status,
        "reason": reason,
        "no_mutants": no_mutants,
        "wall_s": wall_s,
        "returncode": returncode,
        **{
            k: counts[k]
            for k in ("generated", "checked", "killed", "survived", "no_tests", "timeout", "other", "score")
        },
        "on_changed_lines": {
            "checked": len(on_changed),
            "killed": ck,
            "survived": cs,
            "score": _score(ck, cs),
        },
        "mutants": mutants,
        "stdout_tail": output.splitlines()[-30:],
        "tree": str(tree),
    }
