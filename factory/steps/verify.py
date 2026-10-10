"""The Verify step: the QA step, built fully.

In order, each able to stop the run:
1. A fresh headless Claude Code session writes the API tests and the browser tests for the change,
   placed by the application's strategy rule (`factory/prompts/write_tests.md`).
2. Lint: the application's ruff rules plus the no-assertion check (`factory/checks/lint.py`).
3. The revert check: every new test passes at head and fails for a behavioural reason on the
   code before the change (`factory/checks/revert.py`).
4. mutmut 3.8 on the functions the change touched, with the generated API tests alone and with
   the developers' tests added (`factory/checks/mutants.py`).
5. The application's own suite, new tests in place (`factory/checks/suite.py`).
6. A second headless session writes one readable test case per test in the signoff skeleton;
   `factory/checks/cases.py` (a copy of the signoff plugin's linter) checks them.
Then the step stops with a question for Oleg. On re-run with an answer file in the run folder,
the step passes or fails on his answer without redoing the checks.

Every check writes its own JSON under `<run>/verify/`; `report.json` gathers timings, costs and
the artifacts the next steps need.
"""

import ast
import json
import os
import subprocess
import sys
import time

from factory import headless
from factory.checks import lint, mutants, revert, suite

WRITER_MODEL = os.environ.get("QA_FACTORY_WRITER_MODEL", "claude-opus-5-5")
WRITER_BUDGET_USD = float(os.environ.get("QA_FACTORY_WRITER_BUDGET", "5.00"))
CASES_MODEL = os.environ.get("QA_FACTORY_CASES_MODEL", "claude-opus-5-5")
CASES_BUDGET_USD = float(os.environ.get("QA_FACTORY_CASES_BUDGET", "2.00"))
WRITER_TOOLS = "Read,Glob,Grep,Edit,Write,Bash"
WRITER_SETTINGS = {
    "permissions": {
        "deny": [
            "Bash(git commit*)",
            "Bash(git push*)",
            "Bash(git checkout*)",
            "Bash(git reset*)",
            "Bash(git clean*)",
            "Bash(rm -rf*)",
        ]
    }
}
FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES_LINTER = os.path.join(FACTORY_ROOT, "factory", "checks", "cases.py")


class CheckFailed(Exception):
    pass


def _field(inp, name):
    return getattr(inp, name) if hasattr(inp, name) else inp[name]


def _git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL
    )
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])}: {p.stderr.strip()}")
    return p.stdout


def _read(path, default=""):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return default


def _dump(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1, default=str)


def _prompt(name, values):
    with open(os.path.join(FACTORY_ROOT, "factory", "prompts", name + ".md")) as f:
        return f.read().format_map(values)


def _structured_of(artifact_path):
    text = _read(artifact_path, "")
    try:
        return json.dumps(json.loads(text).get("structured"), indent=1)
    except (ValueError, AttributeError):
        return text


def _in_test_dirs(path, app):
    return path.startswith(app["api_tests_dir"] + "/") or path.startswith(app["browser_tests_dir"] + "/")


def _test_ids(tree, relpath):
    """Pytest ids of the tests in a file: file::Class::name for methods, file::name for functions."""
    ids = []
    try:
        module = ast.parse(_read(os.path.join(tree, relpath)))
    except SyntaxError:
        return ids
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith("test"):
                    ids.append(f"{relpath}::{node.name}::{item.name}")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            ids.append(f"{relpath}::{node.name}")
    return ids


# ------------------------------------------------------------------ the checks
def write_tests(ctx):
    app, head_tree, out = ctx["app"], ctx["head_tree"], ctx["out"]
    slug = ctx["slug"]
    api_file = f"test_{slug}_api.py"
    browser_file = app["browser_test_files"].replace("*", slug)
    base, head = ctx["repo"]["base"], ctx["repo"]["head"]

    # Drop whatever an earlier round left in the test folders; keep everything else as it is.
    _git(head_tree, "clean", "-fdq", "--", app["api_tests_dir"], app["browser_tests_dir"])
    _git(head_tree, "checkout", "--", app["api_tests_dir"], app["browser_tests_dir"])

    values = {
        "ticket_json": json.dumps(ctx["ticket"], indent=1),
        "strategy": _read(os.path.join(FACTORY_ROOT, app["strategy"])),
        "diff": _read(ctx["artifacts"].get("change_diff", "")),
        "dev_tests_diff": _git(
            head_tree, "diff", base, head, "--", app["api_tests_dir"], app["browser_tests_dir"]
        ),
        "plan_json": _structured_of(ctx["artifacts"]["plan"]) if "plan" in ctx["artifacts"] else "(no plan)",
        "api_tests_dir": app["api_tests_dir"],
        "browser_tests_dir": app["browser_tests_dir"],
        "api_test_file": api_file,
        "browser_test_file": browser_file,
        "browser_glob": app["browser_test_files"],
        "python": app["python"],
    }
    schema = {
        "type": "object",
        "properties": {"files": {"type": "array", "items": {"type": "string"}}, "notes": {"type": "string"}},
        "required": ["files", "notes"],
    }
    result = headless.call(
        _prompt("write_tests", values),
        cwd=head_tree,
        model=WRITER_MODEL,
        budget_usd=WRITER_BUDGET_USD,
        tools=WRITER_TOOLS,
        allowed_tools=WRITER_TOOLS,
        schema=schema,
        settings=WRITER_SETTINGS,
    )
    ctx["costs"]["write_tests"] = result.metrics()

    status_lines = _git(head_tree, "status", "--porcelain", "--untracked-files=all").splitlines()
    touched_source, modified_tests, new_tests = [], [], []
    for line in status_lines:
        code, path = line[:2], line[3:]
        if not _in_test_dirs(path, app):
            touched_source.append(path)
        elif code.strip() == "??":
            new_tests.append(path)
        else:
            modified_tests.append(path)
    for path in touched_source:  # undo, then fail: the writer may only add tests
        if (
            os.path.exists(os.path.join(head_tree, path))
            and not _git(head_tree, "ls-files", "--", path).strip()
        ):
            os.remove(os.path.join(head_tree, path))
        else:
            _git(head_tree, "checkout", "--", path)
    for path in modified_tests:
        _git(head_tree, "checkout", "--", path)

    manifest = {
        "files": sorted(new_tests),
        "notes": (result.structured or {}).get("notes", "") if isinstance(result.structured, dict) else "",
        "writer_listed": (result.structured or {}).get("files")
        if isinstance(result.structured, dict)
        else None,
        "is_error": result.is_error,
        "result_text": (result.text or "")[-2000:],
        "metrics": result.metrics(),
        "touched_source": touched_source,
        "modified_existing_tests": modified_tests,
    }
    tests_dir = os.path.join(out, "tests")
    for path in new_tests:
        dest = os.path.join(tests_dir, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(os.path.join(head_tree, path)) as src, open(dest, "w") as dst:
            dst.write(src.read())
    manifest_path = os.path.join(out, "tests_manifest.json")
    _dump(manifest_path, manifest)
    ctx["artifacts_out"]["tests_manifest"] = manifest_path
    ctx["artifacts_out"]["tests_dir"] = tests_dir
    ctx["files"] = sorted(new_tests)

    if result.is_error:
        raise CheckFailed(f"test writer ended with an error: {(result.text or '')[:300]}")
    if touched_source:
        raise CheckFailed(f"test writer touched application code (reverted): {touched_source}")
    if modified_tests:
        raise CheckFailed(f"test writer modified existing tests (reverted): {modified_tests}")
    if not new_tests:
        raise CheckFailed("test writer wrote no new test file under the test folders")
    api = [p for p in new_tests if p.startswith(app["api_tests_dir"] + "/")]
    if not api:
        raise CheckFailed("test writer wrote no API test file")
    return {"files": new_tests, "api_files": api, "notes": manifest["notes"]}


def run_lint(ctx):
    report = lint.run(
        ctx["head_tree"], ctx["app"]["python"], ctx["files"], app_package=ctx["app"]["source_package"]
    )
    if report["status"] != "pass":
        rows = "; ".join(f"{f['file']}:{f['line']} {f['rule']}" for f in report["findings"][:10])
        raise CheckFailed(f"lint: {rows}")
    return report


def run_revert(ctx):
    app = ctx["app"]
    with open(ctx["artifacts"]["changed_source"]) as f:
        changed_source = json.load(f)
    report = revert.run(
        ctx["head_tree"],
        ctx["base_tree"],
        changed_source,
        ctx["files"],
        os.path.join(ctx["out"], "revert"),
        app["python"],
        app["pytest_args"],
        app["test_support"],
        app["browser_test_files"],
        app["exclude_copy"],
    )
    if report["status"] != "pass":
        raise CheckFailed(f"revert check: {report['reason']}")
    return report


def run_mutation(ctx):
    app, head_tree, base_tree = ctx["app"], ctx["head_tree"], ctx["base_tree"]
    with open(ctx["artifacts"]["changed_source"]) as f:
        changed_source = json.load(f)
    with open(ctx["artifacts"]["changed_tests"]) as f:
        changed_tests = json.load(f)
    pkg = app["source_package"]
    globs, only_mutate, lines_by_file = [], [], {}
    for row in changed_source:
        path = row["path"]
        if row["status"] not in ("M", "A") or not path.endswith(".py") or not path.startswith(pkg + "/"):
            continue
        if "/migrations/" in path or path.endswith("/__init__.py"):
            continue
        head_src = _read(os.path.join(head_tree, path))
        base_src = _read(os.path.join(base_tree, path)) if row["status"] == "M" else None
        found = mutants.changed_functions(base_src, head_src, path[:-3].replace("/", "."))
        if found:
            globs.extend(found)
            only_mutate.append(path)
            lines_by_file[path] = sorted(mutants.changed_lines(base_src or "", head_src))
    report = {"globs": globs, "only_mutate": only_mutate, "changed_lines": lines_by_file, "runs": {}}
    if not globs:
        report["skipped"] = "the change touched no function body (nothing for mutmut to mutate)"
        return report

    api_files = [p for p in ctx["files"] if p.startswith(app["api_tests_dir"] + "/")]
    dev_api = [
        r["path"]
        for r in changed_tests
        if r["status"] in ("M", "A") and r["path"].startswith(app["api_tests_dir"] + "/")
    ]
    sets = {
        "generated": api_files,
        "generated_and_developers": api_files + [p for p in dev_api if p not in api_files],
    }
    for name, files in sets.items():
        t0 = time.time()
        report["runs"][name] = mutants.run(
            head_tree,
            app["python"],
            pkg,
            only_mutate,
            files,
            globs,
            os.path.join(ctx["out"], "mutation", name),
            app["mutmut"]["pytest_add_cli_args"],
            app["mutmut"]["pre_create_dirs"],
            app["exclude_copy"],
            lines_by_file,
        )
        report["runs"][name]["test_files"] = files
        ctx["timings"][f"mutation.{name}"] = round(time.time() - t0, 1)
    gen = report["runs"]["generated"]
    if gen["status"] != "pass":
        raise CheckFailed(f"mutmut did not run: {gen.get('reason')}")
    if gen.get("generated", 0) and not gen.get("checked", 0):
        raise CheckFailed("mutmut checked no mutant: the generated tests never reach the changed functions")
    changed = gen.get("on_changed_lines", {})
    if gen.get("checked", 0) and changed.get("checked", 0) and changed.get("killed", 0) == 0:
        raise CheckFailed(
            "the generated tests kill no mutant on the changed lines: they do not exercise the change"
        )
    return report


def run_suite(ctx):
    app = ctx["app"]
    report = suite.run(ctx["head_tree"], app["python"], app["suite"], app["pytest_args"])
    if report["status"] != "pass":
        summaries = "; ".join(r.get("summary") or f"rc={r['returncode']}" for r in report["runs"])
        raise CheckFailed(f"the application's suite is red with the new tests: {summaries}")
    return report


def _lint_cases(cases_dir):
    p = subprocess.run(
        [sys.executable, "-I", CASES_LINTER, "check", cases_dir],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def write_cases(ctx):
    app, head_tree, out = ctx["app"], ctx["head_tree"], ctx["out"]
    area = ctx["ticket"].get("area") or app["source_package"]
    cases_dir = os.path.join(out, "testcases")
    os.makedirs(cases_dir, exist_ok=True)
    listing = []
    for path in ctx["files"]:
        for test_id in _test_ids(head_tree, path):
            listing.append(f"- `{test_id}` (source: {path})")
    values = {
        "ticket_json": json.dumps(ctx["ticket"], indent=1),
        "tests_listing": "\n".join(listing) or "(no tests found)",
        "area": area,
        "out_dir": cases_dir,
    }
    schema = {
        "type": "object",
        "properties": {"files": {"type": "array", "items": {"type": "string"}}},
        "required": ["files"],
    }
    tools = "Read,Glob,Grep,Write"
    result = headless.call(
        _prompt("test_cases", values),
        cwd=head_tree,
        model=CASES_MODEL,
        budget_usd=CASES_BUDGET_USD,
        tools=tools,
        allowed_tools=tools,
        schema=schema,
        add_dirs=[cases_dir],
    )
    ctx["costs"]["test_cases"] = result.metrics()
    rc, findings = _lint_cases(cases_dir)
    repair = None
    if rc != 0:
        repair = headless.call(
            "The test cases you wrote under "
            f"{cases_dir} fail their linter. Fix every finding below by editing the files in place; "
            "change nothing else. Respond only through the structured output.\n\n" + findings,
            cwd=head_tree,
            model=CASES_MODEL,
            budget_usd=1.00,
            tools="Read,Glob,Grep,Edit,Write",
            allowed_tools="Read,Glob,Grep,Edit,Write",
            schema=schema,
            add_dirs=[cases_dir],
        )
        ctx["costs"]["test_cases_repair"] = repair.metrics()
        rc, findings = _lint_cases(cases_dir)
    written = sorted(
        os.path.join(root, name)[len(cases_dir) + 1 :]
        for root, _, names in os.walk(cases_dir)
        for name in names
        if name.endswith(".md")
    )
    report = {
        "dir": cases_dir,
        "files": written,
        "test_ids": len(listing),
        "lint_rc": rc,
        "lint": findings,
        "metrics": result.metrics(),
        "repair_metrics": repair.metrics() if repair else None,
    }
    ctx["artifacts_out"]["test_cases"] = cases_dir
    if result.is_error:
        raise CheckFailed(f"test case writer ended with an error: {(result.text or '')[:300]}")
    if rc != 0:
        raise CheckFailed(f"test cases fail their linter: {findings[:500]}")
    if len(written) < len(listing):
        raise CheckFailed(f"{len(written)} test cases for {len(listing)} tests")
    return report


CHECKS = [
    ("write_tests", write_tests),
    ("lint", run_lint),
    ("revert", run_revert),
    ("mutation", run_mutation),
    ("suite", run_suite),
    ("test_cases", write_cases),
]


def _answer(ctx, report_path):
    with open(ctx["artifacts"]["answer"]) as f:
        answer = json.load(f)
    with open(report_path) as f:
        report = json.load(f)
    by = answer.get("by", "a person")
    if answer.get("approved") is True:
        return {
            "status": "pass",
            "artifacts": report["artifacts"],
            "reason": f"approved by {by}: {answer.get('note', '')}".strip(),
            "gate": None,
            "metrics": report.get("metrics", {}),
        }
    return {
        "status": "fail",
        "artifacts": report["artifacts"],
        "reason": f"declined by {by}: {answer.get('note', '')}".strip(),
        "gate": None,
        "metrics": report.get("metrics", {}),
    }


def run(inp):
    repo, ticket, artifacts, run_dir = (_field(inp, k) for k in ("repo", "ticket", "artifacts", "run_dir"))
    app = repo["app"]
    out = os.path.join(run_dir, "verify")
    os.makedirs(out, exist_ok=True)
    report_path = os.path.join(out, "report.json")
    if "answer" in artifacts and os.path.exists(report_path):
        return _answer({"artifacts": artifacts}, report_path)

    slug = ticket["id"]
    if slug.startswith(app["name"] + "-"):
        slug = slug[len(app["name"]) + 1 :]
    ctx = {
        "repo": repo,
        "app": app,
        "ticket": ticket,
        "artifacts": artifacts,
        "run_dir": run_dir,
        "out": out,
        "head_tree": repo["head_tree"],
        "base_tree": repo["base_tree"],
        "slug": slug.replace("-", "_"),
        "files": [],
        "timings": {},
        "costs": {},
        "artifacts_out": {},
    }
    report = {
        "checks": {},
        "timings": ctx["timings"],
        "costs": ctx["costs"],
        "artifacts": ctx["artifacts_out"],
    }
    failure = None
    for name, check in CHECKS:
        t0 = time.time()
        try:
            report["checks"][name] = {"status": "pass", "result": check(ctx)}
        except CheckFailed as e:
            report["checks"][name] = {"status": "fail", "reason": str(e)}
            failure = f"{name}: {e}"
        finally:
            ctx["timings"][name] = round(time.time() - t0, 1)
            _dump(os.path.join(out, name + ".json"), report["checks"].get(name))
        if failure:
            break

    total_cost = sum((m or {}).get("cost_usd") or 0 for m in ctx["costs"].values())
    metrics = {"cost_usd": round(total_cost, 4), "time_s": dict(ctx["timings"]), "costs": dict(ctx["costs"])}
    mut = report["checks"].get("mutation", {}).get("result") or {}
    for name, run_report in (mut.get("runs") or {}).items():
        metrics[f"mutation_score.{name}"] = run_report.get("score")
        metrics[f"mutation_score_changed_lines.{name}"] = (run_report.get("on_changed_lines") or {}).get(
            "score"
        )
    report["metrics"] = metrics
    ctx["artifacts_out"]["verify_report"] = report_path
    _dump(report_path, report)

    if failure:
        return {
            "status": "fail",
            "artifacts": dict(ctx["artifacts_out"]),
            "reason": failure,
            "gate": None,
            "metrics": metrics,
        }

    suite_runs = report["checks"]["suite"]["result"]["runs"]
    context = {
        "tests": ctx["files"],
        "test_files_copy": ctx["artifacts_out"].get("tests_dir"),
        "test_cases": ctx["artifacts_out"].get("test_cases"),
        "revert_check": {k: v["verdict"] for k, v in report["checks"]["revert"]["result"]["tests"].items()},
        "mutation": {
            k: {
                "checked": v.get("checked"),
                "killed": v.get("killed"),
                "survived": v.get("survived"),
                "score": v.get("score"),
                "on_changed_lines": v.get("on_changed_lines"),
            }
            for k, v in (mut.get("runs") or {}).items()
        }
        or mut.get("skipped"),
        "suite": [r.get("summary") for r in suite_runs],
        "cost_usd": metrics["cost_usd"],
        "time_s": metrics["time_s"],
    }
    # The factory does not stop for a person when every check passed (Oleg, 2026-10-10). The
    # approval is recorded as the factory's own; a ticket or app that sets "gate": "person" still
    # stops here, for a risk rule that wants a human.
    gate_mode = ticket.get("gate") or app.get("gate") or "auto"
    if gate_mode == "auto":
        approval_path = os.path.join(out, "approval.json")
        _dump(
            approval_path,
            {"approved": True, "by": "factory", "rule": "every Verify check passed", "context": context},
        )
        ctx["artifacts_out"]["approval"] = approval_path
        _dump(report_path, report)
        return {
            "status": "pass",
            "artifacts": dict(ctx["artifacts_out"]),
            "reason": f"every check passed; approved by the factory ({len(ctx['files'])} test files)",
            "gate": None,
            "metrics": metrics,
        }
    return {
        "status": "needs_person",
        "artifacts": dict(ctx["artifacts_out"]),
        "reason": "the tests and their readable cases are ready for approval",
        "gate": {
            "who": "Oleg",
            "question": f"Approve the generated tests and their test cases for '{ticket['title']}' "
            "so they join the application's suite?",
            "context": context,
        },
        "metrics": metrics,
    }
