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
- mutmut skips every decorated function except one decorated only with `@staticmethod` or
  `@classmethod` (`mutmut/mutation/file_mutation.py`, `_skip_node_and_children`), nested ones
  included. `undecorate` rewrites the copy mutmut mutates so top-level functions and methods get
  mutants (measured on isso 7e91d59: `API.view` 0 -> 30, `API.fetch` 0 -> 238). A function whose
  body is a decorated inner function (`@wraps(func) def wrapper`) still gets none.
- In `pkg/__init__.py` the key drops `__init__`: `pkg.x_f__mutmut_1` (mutmut's `get_mutant_name`;
  measured on isso `isso/utils/__init__.py`).
"""

import ast
import difflib
import json
import os
import shutil
import subprocess
import time
from fnmatch import fnmatchcase
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
    if module.endswith(".__init__"):  # mutmut names the package itself: pkg.x_f, not pkg.__init__.x_f
        module = module[: -len(".__init__")]
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


# Descriptor decorators turn a method into something other than a function; `Cls.m = dec(Cls.m)` after
# the class body is not equivalent for them (a setter needs the property of the same name).
DESCRIPTORS = {"property", "cached_property"}
DESCRIPTOR_ATTRS = {"setter", "getter", "deleter"}


def _decorator_name(dec: ast.expr) -> str:
    node = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else ""


# Decorators a metaclass or class-creation hook reads, or that only make sense while the class body
# runs; applied after the class exists they change behaviour (matched by last attribute or name).
CLASS_TIME = {
    "abstractmethod",
    "validator",
    "field_validator",
    "root_validator",
    "model_validator",
    "validates",
    "declared_attr",
    "hybrid_property",
    "singledispatchmethod",
    "overload",
}


def _class_bound(cls: ast.ClassDef) -> set[str]:
    """Names the class body binds: assignments, function and class definitions."""
    bound: set[str] = set()
    for item in cls.body:
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            bound.add(item.name)
        elif isinstance(item, ast.Assign | ast.AnnAssign | ast.AugAssign):
            for target in item.targets if isinstance(item, ast.Assign) else [item.target]:
                bound.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
    return bound


def _keeps_decorators(node, in_class: bool, names_in_scope: list[str], class_bound=frozenset()) -> str | None:
    """Why the function keeps its decorators, or None when `undecorate` may move them."""
    decs = node.decorator_list
    if any(isinstance(d, ast.Name) and d.id in ("staticmethod", "classmethod") for d in decs):
        return "staticmethod or classmethod"  # alone mutmut handles them; stacked, not measured
    if in_class and any(
        _decorator_name(d) in DESCRIPTORS or (isinstance(d, ast.Attribute) and d.attr in DESCRIPTOR_ATTRS)
        for d in decs
    ):
        return "a descriptor decorator"
    # A name defined twice in one scope (@overload stubs, @x.register on `_`): applying the decorators
    # at the end would see only the last definition.
    if names_in_scope.count(node.name) > 1:
        return "its name is defined twice in its scope"
    hooks = sorted({_decorator_name(d) for d in decs} & CLASS_TIME)
    if hooks:
        return f"@{hooks[0]} is read while the class is created"
    used = sorted({n.id for d in decs for n in ast.walk(d) if isinstance(n, ast.Name)} & class_bound)
    if used:
        return f"its decorator names {', '.join(used)} from the class body"
    return None


def _mutmut_skips(node) -> bool:
    """mutmut mutates a function decorated only with @staticmethod or @classmethod."""
    decs = node.decorator_list
    return not (
        len(decs) == 1 and isinstance(decs[0], ast.Name) and decs[0].id in ("staticmethod", "classmethod")
    )


def undecorate(src: str) -> str:
    """The module with each decorated top-level function and method of a top-level class rewritten
    so mutmut mutates it: every decorator line becomes a comment (`# @dec`, `#` for a continuation
    line) and `f = a(b(f))` or `Cls.m = a(b(Cls.m))` is appended at the end of the module. Every
    existing line keeps its number. Left as they are: `@staticmethod` or `@classmethod` (alone or not),
    descriptor decorators on methods (`@property`, `@x.setter`, ...), a name defined twice in its
    scope, decorators in CLASS_TIME, a method decorator that names something the class body binds,
    and functions nested in functions. A module that does not parse is returned unchanged.
    """
    return undecorate_with_reasons(src)[0]


def undecorate_with_reasons(src: str) -> tuple[str, list[tuple[str, str]]]:
    """`undecorate`, plus (qualified name, reason) for each decorated function it left decorated that
    mutmut then skips (one decorated only with @staticmethod or @classmethod is not listed)."""
    try:
        module = ast.parse(src)
    except SyntaxError:
        return src, []
    lines = src.splitlines(keepends=True)
    defs = (ast.FunctionDef, ast.AsyncFunctionDef)
    targets: list[tuple[ast.AST, str]] = []
    kept: list[tuple[str, str]] = []

    def consider(node, qualified, in_class, names, bound=frozenset()):
        reason = _keeps_decorators(node, in_class, names, bound)
        if reason is None:
            targets.append((node, qualified))
        elif _mutmut_skips(node):
            kept.append((qualified, reason))

    top_names = [n.name for n in module.body if isinstance(n, (*defs, ast.ClassDef))]
    for node in module.body:
        if isinstance(node, defs) and node.decorator_list:
            consider(node, node.name, False, top_names)
        elif isinstance(node, ast.ClassDef):
            names = [i.name for i in node.body if isinstance(i, (*defs, ast.ClassDef))]
            bound = _class_bound(node)
            for item in node.body:
                if isinstance(item, defs) and item.decorator_list:
                    consider(item, f"{node.name}.{item.name}", True, names, bound)
    if not targets:
        return src, kept
    tail = []
    for node, target in targets:
        start = node.decorator_list[0].lineno
        while start > 1 and not lines[start - 1].lstrip().startswith("@"):
            start -= 1  # `@(` on the line before the expression
        for n in range(start, node.lineno):
            text = lines[n - 1]
            indent = text[: len(text) - len(text.lstrip())]
            ending = "\n" if text.endswith("\n") else ""
            stripped = text.strip()
            lines[n - 1] = (
                f"{indent}# {stripped}{ending}" if stripped.startswith("@") else f"{indent}#{ending}"
            )
        expr = target
        for dec in reversed(node.decorator_list):
            callee = ast.unparse(dec)
            if not isinstance(dec, ast.Name | ast.Attribute | ast.Call | ast.Subscript):
                callee = f"({callee})"
            expr = f"{callee}({expr})"
        tail.append(f"{target} = {expr}\n")
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    out = (
        "".join(lines)
        + "\n# Decorators moved here by qa-factory so mutmut mutates the functions.\n"
        + "".join(tail)
    )
    ast.parse(out)  # a broken rewrite fails here, not inside mutmut
    return out, kept


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

    mutmut 3.8.0 makes no mutant for some function shapes (measured on isso 7e91d59: a decorator
    whose body is a decorated inner function); asked only for those by name it aborts with
    NOTHING_MATCHES and exit code 1. That is not a failure of the tests, so it is reported as "no
    mutants" and the caller skips the mutation verdict instead of sending the writer into a repair
    round.
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


def _module_of(relpath: str) -> str:
    module = relpath[:-3].replace("/", ".")
    return module[: -len(".__init__")] if module.endswith(".__init__") else module


def _prepare(head_tree, tree, only_mutate, config, pre_create_dirs, exclude_copy, rewrite):
    """A fresh copy of the head tree with the mutmut config; with `rewrite`, the files to mutate go
    through `undecorate`. Returns (whether a file changed, [(relpath, qualified, reason)] left
    decorated)."""
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(head_tree, tree, ignore=shutil.ignore_patterns(*exclude_copy))
    changed, kept = False, []
    for relpath in only_mutate if rewrite else []:  # the copy only: the worktree keeps its decorators
        source = tree / relpath
        if source.is_file():
            src = source.read_text()
            out, left = undecorate_with_reasons(src)
            if out != src:
                source.write_text(out)
                changed = True
            kept.extend((relpath, qualified, reason) for qualified, reason in left)
    pyproject = tree / "pyproject.toml"
    existing = pyproject.read_text() if pyproject.exists() else ""
    pyproject.write_text(existing + config)
    for d in pre_create_dirs:
        (tree / "mutants" / d).mkdir(parents=True, exist_ok=True)
    return changed, kept


def _invoke(python, tree, globs, timeout):
    """(timed_out, returncode, output, wall seconds) of one `mutmut run`."""
    mutmut = os.path.join(os.path.dirname(str(python)), "mutmut")
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [mutmut, "run", *globs],
            cwd=tree,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result = False, proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        result = True, None, "mutmut timed out"
    return (*result, round(time.monotonic() - start, 2))


def _collect(tree, only_mutate, changed_lines_by_file):
    """(mutants by key, every exit code by key, whether any .meta was found) from a finished run."""
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
    return mutants, all_codes, found_meta


def _broke_before_checking(timed_out, returncode, output, all_codes) -> bool:
    """mutmut stopped before it checked any mutant, and not because nothing matched the globs.

    mutmut 3.8.0 writes every `.meta` while it generates the mutants, before it runs a test, so a
    copy that does not import still leaves a `.meta` with every code null. It then exits 1 after
    pytest fails with "failed to collect stats. runner returned <pytest's code>" (measured: a
    decorator naming a class attribute, `NameError` at import, pytest code 2) or with "Failed to run
    clean test" (`mutmut/__main__.py`, `_run`). The signal used is that pair: a non-zero exit and
    no mutant with an exit code.
    """
    if timed_out or returncode in (0, None) or NOTHING_MATCHES in output:
        return False
    return not any(code is not None for code in all_codes.values())


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
    """Copy the head tree, run mutmut on the chosen mutants and report kills and survivors.

    The copy goes through `undecorate` first. When mutmut then stops before checking any mutant, it
    runs once more on a plain copy and the result says `"undecorate": "fallen back: <reason>"`.
    """
    tree = Path(workdir) / "mutation"
    config = _mutmut_config(only_mutate, test_files, pytest_add_cli_args, source_package)
    rewritten, kept = _prepare(head_tree, tree, only_mutate, config, pre_create_dirs, exclude_copy, True)
    timed_out, returncode, output, wall_s = _invoke(python, tree, globs, timeout)
    mutants, all_codes, found_meta = _collect(tree, only_mutate, changed_lines_by_file)
    fallback = None
    if rewritten and _broke_before_checking(timed_out, returncode, output, all_codes):
        last = next((ln.strip() for ln in reversed(output.splitlines()) if ln.strip()), "")
        fallback = f"fallen back: mutmut exited with code {returncode} and checked no mutant ({last})"
        kept = []  # the plain copy leaves every decorated function decorated
        _prepare(head_tree, tree, only_mutate, config, pre_create_dirs, exclude_copy, False)
        timed_out, returncode, output, again_s = _invoke(python, tree, globs, timeout)
        wall_s = round(wall_s + again_s, 2)
        mutants, all_codes, found_meta = _collect(tree, only_mutate, changed_lines_by_file)

    counts = summarize_meta({"exit_code_by_key": all_codes})
    on_changed = [m for m in mutants.values() if m["changed_line"]]
    ck = sum(m["status"] == "killed" for m in on_changed)
    cs = sum(m["status"] == "survived" for m in on_changed)

    status, reason, no_mutants = classify_exit(timed_out, returncode, found_meta, output, timeout)
    unmutated = [g for g in globs if not any(fnmatchcase(k, g) for k in all_codes)] if found_meta else []
    left_decorated = []
    for relpath, qualified, why in kept:
        cls, _, name = qualified.rpartition(".")
        mangled = f"x{BAR}{cls}{BAR}{name}" if cls else f"x_{name}"
        if any(fnmatchcase(f"{_module_of(relpath)}.{mangled}__mutmut_", g) for g in globs):
            left_decorated.append({"file": relpath, "function": qualified, "reason": why})
    result = {
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
        "unmutated": unmutated,
        "left_decorated": left_decorated,
        "stdout_tail": output.splitlines()[-30:],
        "tree": str(tree),
    }
    if fallback:
        result["undecorate"] = fallback
    return result
