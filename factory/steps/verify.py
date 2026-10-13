"""The Verify step: the QA step, built fully.

One round, each check able to stop it:
1. A fresh headless Claude Code session writes the API tests, and the browser tests when the recipe
   has a browser folder, for the change,
   placed by the application's strategy rule (`factory/prompts/write_tests.md`). In blind mode
   (`"qa_mode": "blind"`) it writes them in the base worktree, without the change, and the files
   are moved into the head worktree (`factory/prompts/write_tests_blind.md`).
2. Lint: the application's ruff rules plus the no-assertion check (`factory/checks/lint.py`).
3. The revert check: every new test passes at head and fails for a behavioural reason on the
   code before the change (`factory/checks/revert.py`).
4. mutmut 3.8 on the functions the change touched, with the generated API tests alone, with the
   developers' tests added, and with the developers' tests alone (`factory/checks/mutants.py`).
5. The application's own suite, new tests in place (`factory/checks/suite.py`).
A failure the writer can fix (lint, revert, mutation) gets one repair round in a fresh session
(`factory/prompts/write_tests_repair.md`). A failure that remains goes to a stronger model
(`factory/escalate.py`), which asks for one guided round, fails the step with its diagnosis, or
stops for a person. Rounds and spend are capped per ticket (`factory/rounds.py`).
Then a second headless session writes one readable test case per test in the signoff skeleton;
`factory/checks/cases.py` (a copy of the signoff plugin's linter) checks them, and the factory
approves the tests itself unless the ticket or app asks for a person.

Every check writes its own JSON under `<run>/verify/rounds/<n>/` and the latest round's under
`<run>/verify/`; `report.json` gathers rounds, timings, costs and the artifacts the next steps need.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import time

from factory import blind, escalate, headless, rounds
from factory.checks import devtests, lint, mutants, revert, suite
from factory.steps.ship import restore_tests

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
            "Bash(git worktree*)",
            "Bash(git -C*)",
            "Bash(git stash*)",
            "Bash(git switch*)",
            "Bash(git restore*)",
            "Bash(npm *)",
            "Bash(npx *)",
            "Bash(yarn*)",
            "Bash(pnpm*)",
            "Bash(rm -rf*)",
        ]
    }
}
FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES_LINTER = os.path.join(FACTORY_ROOT, "factory", "checks", "cases.py")
RUNNER = subprocess.run  # every model call goes through this, so tests replace it (git does not)
FINDINGS_MAX = 8000
BLIND_CHANGE_SECTION = (
    "## The change\n\nThe change is in this tree. Its diff is not given: work from the findings, the "
    "ticket and the code."
)
RULE_VERIFY = "every Verify check passed"
RULE_REVIEW_FIX = "every check passed after the review's fix round"


class CheckFailed(Exception):
    def __init__(self, message, repairable: bool = False, report=None):
        super().__init__(message)
        self.repairable = repairable
        self.report = report


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


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return None


def _dump(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1, default=str)


def _prompt(name, values):
    values = {"browser_section": "", **values}
    with open(os.path.join(FACTORY_ROOT, "factory", "prompts", name + ".md")) as f:
        return f.read().format_map(values)


NO_BROWSER_SECTION = "This application has no browser tests in Python: write API tests only."

_PYTEST = '`{python} -m pytest -p no:cacheprovider{flags} -o "python_files={browser_glob}" '
_BROWSER_FILE = "{browser_tests_dir}/{browser_test_file}`."

_BROWSER_COMMON = """Browser tests.

- Also read `{browser_tests_dir}/helpers.py` and one existing test file in that folder.
- Write the browser test(s) into `{browser_tests_dir}/{browser_test_file}`. New file only, that name
  exactly."""

_BROWSER_SECTIONS = {
    "fresh": _BROWSER_COMMON
    + """
- In the browser test, first assert the new control is present, then use it and assert the visible
  result.
- Run it and make it pass:
  """
    + _PYTEST.replace("{flags}", "")
    + _BROWSER_FILE,
    "blind": _BROWSER_COMMON
    + """
- The browser test cannot run here (the assets are not built). Check that it collects:
  """
    + _PYTEST.replace("{flags}", " --collect-only -q")
    + _BROWSER_FILE
    + """
- In it, first assert the new control is present, then use it and assert the visible result.""",
    "repair": "Browser tests. Run the browser test file too and make it pass:\n"
    + _PYTEST.replace("{flags}", "")
    + _BROWSER_FILE,
}


def _browser_section(app, mode, values):
    """The writer prompt's browser instructions for `mode`, or the one line that says there are none."""
    if not browser_dir(app):
        return NO_BROWSER_SECTION
    return _BROWSER_SECTIONS[mode].format_map(values)


def _structured_of(artifact_path):
    text = _read(artifact_path, "")
    try:
        return json.dumps(json.loads(text).get("structured"), indent=1)
    except (ValueError, AttributeError):
        return text


def browser_dir(app):
    """The recipe's browser test folder, or None for an application with no browser tests in Python."""
    return app.get("browser_tests_dir") or None


def test_dirs(app):
    """The folders that hold tests: the API folder, then the browser folder when there is one."""
    return [d for d in (app["api_tests_dir"], browser_dir(app)) if d]


def _in_test_dirs(path, app):
    return any(path.startswith(d + "/") for d in test_dirs(app))


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


def _cost_key(ctx):
    return "write_tests" if ctx["kind"] == "write" else f"{ctx['kind']}.r{ctx['round']}"


def _record(ctx, key, ledger_kind, metrics):
    """Keep one model call's metrics in ctx["costs"] and in the ticket's ledger."""
    metrics = metrics or {}
    ctx["costs"][key] = metrics
    ctx["ledger"].add(
        "verify",
        ledger_kind,
        float(metrics.get("cost_usd") or 0.0),
        metrics.get("model") or "",
        round((metrics.get("duration_ms") or 0) / 1000, 1),
        round=ctx.get("round"),
    )


# ------------------------------------------------------------------ the checks
def _clean_tests(tree, app):
    """Drop whatever an earlier round left in the test folders; keep everything else as it is."""
    dirs = test_dirs(app)
    _git(tree, "clean", "-fdq", "--", *dirs)
    tracked = [d for d in dirs if _git(tree, "ls-files", "--", d).strip()]  # checkout fails on others
    if tracked:
        _git(tree, "checkout", "--", *tracked)


def _content(tree, path):
    try:
        with open(os.path.join(tree, path), "rb") as f:
            return f.read()
    except OSError:
        return None


def _status(tree):
    """(code, path) for every changed path in `tree`, read with -z so no path comes back quoted."""
    entries = _git(tree, "status", "--porcelain", "-z", "--untracked-files=all").split("\0")
    out, i = [], 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":  # a rename or copy: the next entry is the old path
            i += 1
        out.append((code, path))
    return out


def _snapshot(tree, app):
    """What is already changed in `tree` before the writer runs, other than new tests: {path: content}.

    Preparing a tree can leave files changed (`npm install` rewrote linkding's package-lock.json at
    573b6f5), and the writer must not be blamed for them, nor may they be undone.
    """
    return {
        path: _content(tree, path)
        for code, path in _status(tree)
        if not (code.strip() == "??" and _in_test_dirs(path, app))
    }


def _sort_status(tree, app, before=None):
    """Undo what the writer may not do in `tree`; return (touched source, modified tests, new tests).

    `before` is the `_snapshot` taken before the writer ran; a path changed then and not since is
    not the writer's doing.
    """
    before = before or {}
    touched_source, modified_tests, new_tests = [], [], []
    for code, path in _status(tree):
        if path in before and before[path] == _content(tree, path):
            continue
        if not _in_test_dirs(path, app):
            touched_source.append(path)
        elif code.strip() == "??":
            new_tests.append(path)
        else:
            modified_tests.append(path)
    for path in touched_source + modified_tests:  # undo, then fail: the writer may only add tests
        if path in before:  # changed before the writer ran: put back what was there then
            if before[path] is None:
                if os.path.exists(os.path.join(tree, path)):
                    os.remove(os.path.join(tree, path))
            else:
                with open(os.path.join(tree, path), "wb") as f:
                    f.write(before[path])
        elif os.path.exists(os.path.join(tree, path)) and not _git(tree, "ls-files", "--", path).strip():
            os.remove(os.path.join(tree, path))
        else:
            _git(tree, "checkout", "--", path)
    return touched_source, modified_tests, new_tests


def _writer_prompt(ctx):
    app, head_tree = ctx["app"], ctx["head_tree"]
    values = {
        "strategy": _read(os.path.join(FACTORY_ROOT, app["strategy"])),
        "api_tests_dir": app["api_tests_dir"],
        "api_helpers": app.get("test_helpers") or app["api_tests_dir"] + "/helpers.py",
        "api_test_file": f"test_{ctx['slug']}_api.py",
        "python": app["python"],
    }
    if browser_dir(app):
        values.update(
            browser_tests_dir=browser_dir(app),
            browser_test_file=app["browser_test_files"].replace("*", ctx["slug"]),
            browser_glob=app["browser_test_files"],
        )
    mode = "repair" if ctx["mode"] == "repair" else "blind" if ctx["blind"] else "fresh"
    values["browser_section"] = _browser_section(app, mode, values)
    ticket = blind.public_ticket(ctx["ticket"]) if ctx["blind"] else ctx["ticket"]
    diff = _read(ctx["artifacts"].get("change_diff", ""))
    plan = _structured_of(ctx["artifacts"]["plan"]) if "plan" in ctx["artifacts"] else "(no plan)"
    if ctx["mode"] == "repair":
        change = (
            BLIND_CHANGE_SECTION
            if ctx["blind"]
            else f"## The change (source files only)\n\n```diff\n{diff}\n```"
        )
        values.update(
            ticket_json=json.dumps(ticket, indent=1),
            change_section=change,
            files="\n".join(ctx["files"]) or "(none)",
            findings=ctx["findings"] or "(none)",
            guidance=ctx["guidance"] or "(none)",
        )
        return _prompt("write_tests_repair", values)
    if ctx["blind"]:
        values.update(ticket_json=json.dumps(ticket, indent=1), plan_json=plan)
        return _prompt("write_tests_blind", values)
    base, head = ctx["repo"]["base"], ctx["repo"]["head"]
    values.update(
        ticket_json=json.dumps(ticket, indent=1),
        diff=diff,
        dev_tests_diff=_git(head_tree, "diff", base, head, "--", *test_dirs(app)),
        plan_json=plan,
    )
    return _prompt("write_tests", values)


def write_tests(ctx):
    app, head_tree, base_tree, out = ctx["app"], ctx["head_tree"], ctx["base_tree"], ctx["out"]
    round_dir = os.path.join(out, "rounds", str(ctx["round"]))
    fresh = ctx["mode"] == "fresh"
    blind_fresh = fresh and ctx["blind"]

    if fresh:
        _clean_tests(head_tree, app)
    if blind_fresh:
        _clean_tests(base_tree, app)
    cwd, settings, transcript, hidden = head_tree, WRITER_SETTINGS, None, []
    if blind_fresh:
        hidden = blind.hidden_paths(ctx["repo"], FACTORY_ROOT)
        cwd, settings = base_tree, blind.settings(hidden, base=WRITER_SETTINGS)
        transcript = os.path.join(round_dir, "writer.jsonl")
    schema = {
        "type": "object",
        "properties": {"files": {"type": "array", "items": {"type": "string"}}, "notes": {"type": "string"}},
        "required": ["files", "notes"],
    }
    before = _snapshot(cwd, app)
    result = headless.call(
        _writer_prompt(ctx),
        cwd=cwd,
        model=WRITER_MODEL,
        budget_usd=ctx["ledger"].budget_for(WRITER_BUDGET_USD),
        tools=WRITER_TOOLS,
        allowed_tools=WRITER_TOOLS,
        schema=schema,
        settings=settings,
        transcript_path=transcript,
        runner=RUNNER,
    )
    ctx["costs"][_cost_key(ctx)] = result.metrics()  # _attempt puts it in the ledger

    touched_source, modified_tests, new_tests = _sort_status(cwd, app, before)
    clashes = []
    if blind_fresh:  # move the new files into the change's tree and leave the base tree as it was
        for path in new_tests:
            target = os.path.join(head_tree, path)
            if os.path.exists(target):  # the change has a file of that name: never overwrite it
                clashes.append(path)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(os.path.join(base_tree, path), target)
        new_tests = [p for p in new_tests if p not in clashes]
        _clean_tests(base_tree, app)

    structured = result.structured if isinstance(result.structured, dict) else {}
    manifest = {
        "files": sorted(new_tests),
        "notes": structured.get("notes", ""),
        "writer_listed": structured.get("files") if structured else None,
        "is_error": result.is_error,
        "result_text": (result.text or "")[-2000:],
        "metrics": result.metrics(),
        "touched_source": touched_source,
        "modified_existing_tests": modified_tests,
        "round": ctx["round"],
        "kind": ctx["kind"],
        "cwd": cwd,
    }
    if blind_fresh:
        manifest["blind_clashes"] = clashes
        manifest["blind_audit"] = blind.audit(transcript, hidden, allowed=[app["python"]])
    tests_dir = os.path.join(out, "tests")
    shutil.rmtree(tests_dir, ignore_errors=True)
    for dest_root in (tests_dir, os.path.join(round_dir, "tests")):
        for path in new_tests:
            dest = os.path.join(dest_root, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(os.path.join(head_tree, path), dest)
    manifest_path = os.path.join(out, "tests_manifest.json")
    _dump(manifest_path, manifest)
    _dump(os.path.join(round_dir, "tests_manifest.json"), manifest)
    ctx["artifacts_out"]["tests_manifest"] = manifest_path
    ctx["artifacts_out"]["tests_dir"] = tests_dir
    ctx["files"] = sorted(new_tests)

    if result.is_error:
        raise CheckFailed(f"test writer ended with an error: {(result.text or result.stderr or '')[:300]}")
    if touched_source:
        raise CheckFailed(f"test writer touched application code (reverted): {touched_source}")
    if modified_tests:
        raise CheckFailed(f"test writer modified existing tests (reverted): {modified_tests}")
    if clashes:
        raise CheckFailed(f"the blind test writer's files exist in the change (not copied): {clashes}")
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
        raise CheckFailed(f"lint: {rows}", repairable=True, report=report)
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
        app.get("browser_test_files") if browser_dir(app) else None,
        app["exclude_copy"],
    )
    if report["status"] != "pass":
        # With no test result (pytest ended without one, or timed out) there is nothing to repair.
        raise CheckFailed(
            f"revert check: {report['reason']}", repairable=bool(report["tests"]), report=report
        )
    return report


def run_developers_revert(ctx):
    """The revert check on the developers' own new tests: reported, never a failure, once per run."""
    if "developers_revert" in ctx:
        return ctx["developers_revert"]
    app = ctx["app"]
    with open(ctx["artifacts"]["changed_source"]) as f:
        changed_source = json.load(f)
    with open(ctx["artifacts"]["changed_tests"]) as f:
        changed_tests = json.load(f)
    ctx["developers_revert"] = devtests.run(
        ctx["head_tree"],
        ctx["base_tree"],
        changed_source,
        changed_tests,
        os.path.join(ctx["out"], "developers_revert"),
        app["python"],
        app["pytest_args"],
        app["test_support"],
        app.get("browser_test_files") if browser_dir(app) else None,
        app["exclude_copy"],
    )
    return ctx["developers_revert"]


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
    if dev_api:
        sets["developers"] = dev_api
    for name, files in sets.items():
        if name == "developers" and "developers_mutation" in ctx:  # the developers' tests do not change
            report["runs"][name] = ctx["developers_mutation"]
            continue
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
        if name == "generated" and report["runs"][name].get("no_mutants"):
            report["skipped"] = f"{report['runs'][name]['reason']}: {', '.join(globs)}"
            return report
        if name == "developers":
            ctx["developers_mutation"] = report["runs"][name]
    gen = report["runs"]["generated"]
    if gen["status"] != "pass":
        raise CheckFailed(f"mutmut did not run: {gen.get('reason')}", report=report)
    if gen.get("generated", 0) and not gen.get("checked", 0):
        raise CheckFailed(
            "mutmut checked no mutant: the generated tests never reach the changed functions",
            repairable=True,
            report=report,
        )
    changed = gen.get("on_changed_lines", {})
    if gen.get("checked", 0) and changed.get("checked", 0) and changed.get("killed", 0) == 0:
        raise CheckFailed(
            "the generated tests kill no mutant on the changed lines: they do not exercise the change",
            repairable=True,
            report=report,
        )
    return report


def run_suite(ctx):
    app = ctx["app"]
    report = suite.run(ctx["head_tree"], app["python"], app["suite"], app["pytest_args"])
    if report["status"] != "pass":
        summaries = "; ".join(r.get("summary") or f"rc={r['returncode']}" for r in report["runs"])
        raise CheckFailed(f"the application's suite is red with the new tests: {summaries}", report=report)
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
    shutil.rmtree(cases_dir, ignore_errors=True)  # a later round's cases replace the earlier ones
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
        budget_usd=ctx["ledger"].budget_for(CASES_BUDGET_USD),
        tools=tools,
        allowed_tools=tools,
        schema=schema,
        add_dirs=[cases_dir],
        runner=RUNNER,
    )
    _record(ctx, "test_cases", "cases", result.metrics())
    rc, findings = _lint_cases(cases_dir)
    repair = None
    if rc != 0:
        repair = headless.call(
            "The test cases you wrote under "
            f"{cases_dir} fail their linter. Fix every finding below by editing the files in place; "
            "change nothing else. Respond only through the structured output.\n\n" + findings,
            cwd=head_tree,
            model=CASES_MODEL,
            budget_usd=ctx["ledger"].budget_for(1.00),
            tools="Read,Glob,Grep,Edit,Write",
            allowed_tools="Read,Glob,Grep,Edit,Write",
            schema=schema,
            add_dirs=[cases_dir],
            runner=RUNNER,
        )
        _record(ctx, "test_cases_repair", "cases_repair", repair.metrics())
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


def restore_round(ctx):
    """A recheck round's first stage: an earlier round's tests put back as they were; no writer call.

    For after a fix to the environment or to the factory itself, so the same tests are judged again.
    """
    app, head_tree, out, n = ctx["app"], ctx["head_tree"], ctx["out"], ctx["recheck_round"]
    source = os.path.join(out, "rounds", str(n))
    files = list((_load(os.path.join(source, "tests_manifest.json")) or {}).get("files") or [])
    if not files or not all(os.path.isfile(os.path.join(source, "tests", p)) for p in files):
        raise CheckFailed(f"round {n} kept no tests to check again")
    written = _load(os.path.join(source, "write_tests.json")) or {}
    if written.get("status") != "pass":  # the writer's own checks: an API file, no error, no clash
        raise CheckFailed(f"round {n}'s tests failed the writer's own checks: {written.get('reason', '')}")
    _clean_tests(head_tree, app)
    round_dir = os.path.join(out, "rounds", str(ctx["round"]))
    tests_dir = os.path.join(out, "tests")
    shutil.rmtree(tests_dir, ignore_errors=True)
    for dest_root in (head_tree, tests_dir, os.path.join(round_dir, "tests")):
        for path in files:
            dest = os.path.join(dest_root, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(os.path.join(source, "tests", path), dest)
    manifest = {"files": files, "rechecked_round": n, "round": ctx["round"], "kind": "recheck"}
    manifest_path = os.path.join(out, "tests_manifest.json")
    _dump(manifest_path, manifest)
    _dump(os.path.join(round_dir, "tests_manifest.json"), manifest)
    ctx["artifacts_out"]["tests_manifest"] = manifest_path
    ctx["artifacts_out"]["tests_dir"] = tests_dir
    ctx["files"] = files
    return {"files": files, "rechecked_round": n}


ATTEMPT_CHECKS = [
    ("write_tests", write_tests),
    ("lint", run_lint),
    ("revert", run_revert),
    ("developers_revert", run_developers_revert),
    ("mutation", run_mutation),
    ("suite", run_suite),
]
FINAL_CHECKS = [("test_cases", write_cases)]


# ------------------------------------------------------------------ the rounds
def _context(inp, previous=None):
    """Everything one Verify run carries. `previous` is an earlier report.json this run continues."""
    repo, ticket, artifacts, run_dir = (_field(inp, k) for k in ("repo", "ticket", "artifacts", "run_dir"))
    app = repo["app"]
    out = os.path.join(run_dir, "verify")
    os.makedirs(out, exist_ok=True)
    slug = ticket["id"]
    if slug.startswith(app["name"] + "-"):
        slug = slug[len(app["name"]) + 1 :]
    rounds_dir = os.path.join(out, "rounds")
    done = [int(n) for n in os.listdir(rounds_dir) if n.isdigit()] if os.path.isdir(rounds_dir) else []
    previous = previous or {}
    return {
        "repo": repo,
        "app": app,
        "ticket": ticket,
        "artifacts": artifacts,
        "run_dir": run_dir,
        "out": out,
        "report_path": os.path.join(out, "report.json"),
        "head_tree": repo["head_tree"],
        "base_tree": repo["base_tree"],
        "slug": slug.replace("-", "_"),
        "files": [],
        "timings": {},
        "costs": {},
        "artifacts_out": dict(previous.get("artifacts") or {}),
        "checks": {},
        "ledger": rounds.Ledger(run_dir, rounds.caps_for(ticket, app)),
        "blind": blind.is_blind(ticket),
        "rounds": list(previous.get("rounds") or []),
        "history": [
            {k: r.get(k) for k in ("round", "kind", "failure")} for r in previous.get("history") or []
        ],
        "advice": list(previous.get("advice") or []),
        "attempts": 0,
        "repaired": False,
        "guided": False,
        "recheck_round": None,
        "round_no": max(done, default=0) + 1,
        "round": None,
        "kind": None,
        "mode": "fresh",
        "findings": "",
        "guidance": "",
    }


def _metrics(ctx):
    total = sum((m or {}).get("cost_usd") or 0 for m in ctx["costs"].values())
    metrics = {
        "cost_usd": round(total, 4),
        "time_s": dict(ctx["timings"]),
        "costs": dict(ctx["costs"]),
        "rounds": ctx["attempts"],
        "ticket_spent_usd": rounds.round_4(ctx["ledger"].spent()),
    }
    mut = ctx["checks"].get("mutation", {}).get("result") or {}
    for name, run_report in (mut.get("runs") or {}).items():
        metrics[f"mutation_score.{name}"] = run_report.get("score")
        metrics[f"mutation_score_changed_lines.{name}"] = (run_report.get("on_changed_lines") or {}).get(
            "score"
        )
    return metrics


def _write_report(ctx):
    ctx["artifacts_out"]["verify_report"] = ctx["report_path"]
    first = _load(os.path.join(ctx["out"], "rounds", "1", "tests_manifest.json")) or {}
    report = {
        "checks": ctx["checks"],
        "timings": ctx["timings"],
        "costs": ctx["costs"],
        "artifacts": ctx["artifacts_out"],
        "metrics": _metrics(ctx),
        "rounds": ctx["rounds"],
        "history": ctx["history"],
        "advice": ctx["advice"],
        "ledger": ctx["ledger"].summary(),
        "blind": ctx["blind"],
        "blind_audit": first.get("blind_audit"),
        "gate_kind": ctx.get("gate_kind"),
        "last_failure": ctx.get("last_failure"),
        "status": ctx.get("status"),
    }
    _dump(ctx["report_path"], report)
    return report


def _attempt(ctx, kind, findings="", guidance=""):
    """One round of ATTEMPT_CHECKS; returns the failure or None."""
    n = ctx["round_no"]
    ctx["round_no"] = n + 1
    ctx["attempts"] += 1
    ctx.update(round=n, kind=kind, mode="fresh" if kind == "write" else "repair")
    ctx.update(findings=findings, guidance=guidance, checks={})
    round_dir = os.path.join(ctx["out"], "rounds", str(n))
    os.makedirs(round_dir, exist_ok=True)
    summary, failure = {}, None
    checks = ATTEMPT_CHECKS
    if kind == "recheck":  # the tests of an earlier round, no writer
        checks = [("write_tests", restore_round)] + [c for c in ATTEMPT_CHECKS if c[0] != "write_tests"]
    for name, check in checks:
        t0 = time.time()
        try:
            entry = {"status": "pass", "result": check(ctx)}
        except CheckFailed as e:
            entry = {"status": "fail", "reason": str(e), "repairable": e.repairable}
            if e.report is not None:
                entry["result"] = e.report
        secs = round(time.time() - t0, 1)
        ctx["timings"][name if kind == "write" else f"{name}.r{n}"] = secs
        if name == "write_tests" and kind != "recheck":  # a writer call is a round even at no cost
            metrics = ctx["costs"].get(_cost_key(ctx)) or {}
            _record(ctx, _cost_key(ctx), "write" if kind == "write" else kind, metrics)
        ctx["checks"][name] = entry
        path = os.path.join(round_dir, name + ".json")
        _dump(path, entry)
        _dump(os.path.join(ctx["out"], name + ".json"), entry)
        summary[name] = {"status": entry["status"], "s": secs}
        if entry["status"] == "fail":
            failure = {
                "check": name,
                "reason": entry["reason"],
                "repairable": entry["repairable"],
                "report": path,
            }
            break
    ctx["rounds"].append({"round": n, "kind": kind, "checks": summary, "failure": failure})
    ctx["history"].append({"round": n, "kind": kind, "failure": failure["reason"] if failure else None})
    _write_report(ctx)
    return failure


def _source_line(tree, key, files, line):
    """The head tree's text of `line` in the file whose module the mutant key names."""
    module = key.rsplit(".", 1)[0]
    for path in files:
        if path[:-3].replace("/", ".") == module:
            lines = _read(os.path.join(tree, path)).splitlines()
            return lines[line - 1].strip() if 0 < line <= len(lines) else ""
    return ""


def _findings(ctx, failure):
    """Plain text for the writer from the failing round's check JSON."""
    entry = _load(failure.get("report")) or {}
    result = entry.get("result") or {}
    check = failure.get("check")
    out = [f"The check `{check}` failed: {failure.get('reason', '')}"]
    if check == "lint":
        for f in result.get("findings") or []:
            out.append(f"{f.get('file')}:{f.get('line')} {f.get('rule')} {f.get('message')}")
    elif check == "revert":
        tests = result.get("tests") or {}
        for nodeid, t in tests.items():
            if t.get("verdict") in ("proves-behaviour", "passes-without-change"):
                continue
            out.append(
                f"{nodeid}: {t.get('verdict')} (at head: {t.get('at_head')}, without the change: "
                f"{t.get('reverted')}): {(t.get('message') or '')[:300]}"
            )
        if tests and not any(t.get("verdict") == "proves-behaviour" for t in tests.values()):
            out.append("No test fails on an assertion when the change is taken out.")
    elif check == "mutation":
        gen = (result.get("runs") or {}).get("generated") or {}
        changed = gen.get("on_changed_lines") or {}
        out.append(
            f"on the changed lines: checked {changed.get('checked', 0)}, killed {changed.get('killed', 0)}, "
            f"survived {changed.get('survived', 0)}"
        )
        survivors = [
            (key, m)
            for key, m in (gen.get("mutants") or {}).items()
            if m.get("changed_line") and m.get("status") == "survived" and m.get("line")
        ]
        for key, m in survivors[:10]:
            line = m["line"]
            text = _source_line(ctx["head_tree"], key, result.get("only_mutate") or [], line)
            out.append(f"line {line}: {text}")
    elif check == "suite":
        for r in result.get("runs") or []:
            out.append(f"run: {r.get('summary') or 'rc=' + str(r.get('returncode'))}")
            if r.get("returncode") != 0:
                out.extend(r.get("tail") or [])
    return "\n".join(out)[:FINDINGS_MAX]


def _fail(ctx, reason):
    ctx["status"] = "fail"
    report = _write_report(ctx)
    return {
        "status": "fail",
        "artifacts": dict(ctx["artifacts_out"]),
        "reason": reason,
        "gate": None,
        "metrics": report["metrics"],
    }


def _advise(ctx, failure, allow_retry):
    """One stronger-model call; its record is kept as verify/escalation-<k>.json."""
    ledger = ctx["ledger"]
    k = ledger.count("advice") + 1
    path = os.path.join(ctx["out"], f"escalation-{k}.json")
    record = escalate.decide(
        ticket=ctx["ticket"],
        strategy=_read(os.path.join(FACTORY_ROOT, ctx["app"].get("strategy", ""))),
        diff=_read(ctx["artifacts"].get("change_diff", "")),
        failure=failure,
        history=ctx["history"],
        test_files=ctx["files"],
        head_tree=ctx["head_tree"],
        run_dir=ctx["run_dir"],
        allow_retry=allow_retry,
        budget_usd=ledger.budget_for(escalate.BUDGET_USD, minimum=min(escalate.MIN_USD, escalate.BUDGET_USD)),
        out_path=path,
        runner=RUNNER,
    )
    metrics = record.get("metrics") or {}
    ctx["costs"][f"advice.{k}"] = metrics
    ledger.add(
        "verify",
        "advice",
        float(metrics.get("cost_usd") or 0.0),
        metrics.get("model") or escalate.MODEL,
        round((metrics.get("duration_ms") or 0) / 1000, 1),
        outcome=record["decision"],
    )
    ctx["advice"].append(path)
    ctx["artifacts_out"]["escalation"] = path
    return record


def _escalation_gate(ctx, failure, record):
    ctx["gate_kind"], ctx["last_failure"], ctx["status"] = "escalation", failure, "needs_person"
    report = _write_report(ctx)
    return {
        "status": "needs_person",
        "artifacts": dict(ctx["artifacts_out"]),
        "reason": f"the stronger model could not decide about {failure['check']}: {record.get('why', '')}",
        "gate": {
            "who": "Oleg",
            "question": f"Verify still fails for '{ctx['ticket']['title']}' ({failure['check']}: "
            f"{failure['reason'][:300]}) and the stronger model could not decide. Answer with "
            '{"decision": "retry", "guidance": "<what the writer should do>", "by": "Oleg"} for one '
            'more guided round; {"decision": "recheck", "round": <n>, "by": "Oleg"} to check the tests of '
            "round n again with no writer call, after fixing the environment or the factory; or any other "
            'decision (for example "change_is_wrong") with a "note" to fail the step.',
            "context": {
                "kind": "escalation",
                "failure": failure,
                "why": record.get("why", ""),
                "escalation": ctx["artifacts_out"].get("escalation"),
                "rounds": ctx["history"],
                "ledger": report["ledger"],
            },
        },
        "metrics": report["metrics"],
    }


def _settle(ctx, failure):
    """Repair, ask the stronger model, retry, until an attempt passes (None) or the step ends."""
    ledger = ctx["ledger"]
    while failure:
        if failure["repairable"] and not ctx["repaired"] and ledger.rounds_left() > 0:
            ctx["repaired"] = True
            failure = _attempt(ctx, "repair", findings=_findings(ctx, failure))
            continue
        last = f"{failure['check']}: {failure['reason']}"
        if ledger.advice_left() <= 0:
            cap = ledger.caps["advice"]
            return _fail(ctx, f"{last} (the cap of {cap} stronger-model calls on this ticket was reached)")
        allow_retry = not ctx["guided"] and ledger.rounds_left() > 0
        record = _advise(ctx, failure, allow_retry)
        decision, diagnosis = record["decision"], record.get("diagnosis") or record.get("why", "")
        if decision == "retry" and allow_retry:
            ctx["guided"] = True
            failure = _attempt(
                ctx, "guided", findings=_findings(ctx, failure), guidance=record.get("guidance", "")
            )
            continue
        if decision == "change_is_wrong":
            return _fail(ctx, f"the stronger model judged the tests right and the change wrong: {diagnosis}")
        if decision == "environment":
            return _fail(ctx, f"environment problem, diagnosed by the stronger model: {diagnosis}")
        return _escalation_gate(ctx, failure, record)
    return None


def _approve(ctx, rule):
    ticket, app = ctx["ticket"], ctx["app"]
    report = _write_report(ctx)
    metrics = report["metrics"]
    mut = ctx["checks"].get("mutation", {}).get("result") or {}
    context = {
        "tests": ctx["files"],
        "test_files_copy": ctx["artifacts_out"].get("tests_dir"),
        "test_cases": ctx["artifacts_out"].get("test_cases"),
        "revert_check": {k: v["verdict"] for k, v in ctx["checks"]["revert"]["result"]["tests"].items()},
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
        "suite": [r.get("summary") for r in ctx["checks"]["suite"]["result"]["runs"]],
        "cost_usd": metrics["cost_usd"],
        "time_s": metrics["time_s"],
    }
    # The factory does not stop for a person when every check passed (Oleg, 2026-10-10). The
    # approval is recorded as the factory's own; a ticket or app that sets "gate": "person" still
    # stops here, for a risk rule that wants a human.
    gate_mode = ticket.get("gate") or app.get("gate") or "auto"
    if gate_mode == "auto":
        ctx["status"] = "pass"
        approval_path = os.path.join(ctx["out"], "approval.json")
        _dump(approval_path, {"approved": True, "by": "factory", "rule": rule, "context": context})
        ctx["artifacts_out"]["approval"] = approval_path
        _write_report(ctx)
        return {
            "status": "pass",
            "artifacts": dict(ctx["artifacts_out"]),
            "reason": f"every check passed; approved by the factory ({len(ctx['files'])} test files)",
            "gate": None,
            "metrics": metrics,
        }
    ctx["gate_kind"], ctx["status"] = "approval", "needs_person"
    _write_report(ctx)
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


def _finish(ctx, failure, rule):
    """After the first attempt: settle its failure, write the test cases, approve."""
    terminal = _settle(ctx, failure)
    if terminal:
        return terminal
    for name, check in FINAL_CHECKS:
        t0 = time.time()
        try:
            entry = {"status": "pass", "result": check(ctx)}
        except CheckFailed as e:
            entry = {"status": "fail", "reason": str(e)}
        ctx["timings"][name] = round(time.time() - t0, 1)
        ctx["checks"][name] = entry
        _dump(os.path.join(ctx["out"], name + ".json"), entry)
        if entry["status"] == "fail":
            return _fail(ctx, f"{name}: {entry['reason']}")
    return _approve(ctx, rule)


def _guarded(ctx, step):
    try:
        return step()
    except rounds.CapReached as e:
        return _fail(ctx, str(e))


def _restore(ctx, artifacts):
    """Put the tests of an earlier round back into the head tree; ctx["files"] from its manifest."""
    manifest = _load(artifacts.get("tests_manifest")) or {}
    ctx["files"] = list(manifest.get("files") or [])
    restore_tests(ctx["head_tree"], ctx["files"], artifacts.get("tests_dir"))


def _answer(inp, report_path):
    artifacts = _field(inp, "artifacts")
    with open(artifacts["answer"]) as f:
        answer = json.load(f)
    with open(report_path) as f:
        report = json.load(f)
    by = answer.get("by", "a person")
    done = {"artifacts": report["artifacts"], "gate": None, "metrics": report.get("metrics", {})}

    def ended(status, reason):
        report["status"] = status
        _dump(report_path, report)
        return {"status": status, "reason": reason.strip(), **done}

    if (report.get("gate_kind") or "approval") == "approval":
        if answer.get("approved") is True:
            return ended("pass", f"approved by {by}: {answer.get('note', '')}")
        return ended("fail", f"declined by {by}: {answer.get('note', '')}")
    decision = answer.get("decision")
    if decision == "recheck":  # the environment or the factory was fixed: judge the same tests again
        ctx = _context(inp, previous=report)
        kinds = {r.get("kind") for r in ctx["rounds"]}
        ctx["repaired"], ctx["guided"] = "repair" in kinds, "guided" in kinds
        n = answer.get("round")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            return ended("fail", f"decided by {by}: recheck without a round number (got {n!r})")
        ctx["recheck_round"] = n
        return _guarded(ctx, lambda: _finish(ctx, _attempt(ctx, "recheck"), RULE_VERIFY))
    if decision != "retry":
        note = answer.get("guidance") or answer.get("note") or ""
        return ended("fail", f"decided by {by}: {decision}: {note}")
    ctx = _context(inp, previous=report)
    ctx["repaired"] = ctx["guided"] = True
    _restore(ctx, report["artifacts"])
    findings = _findings(ctx, report.get("last_failure") or {})
    guidance = answer.get("guidance", "")
    return _guarded(
        ctx, lambda: _finish(ctx, _attempt(ctx, "guided", findings=findings, guidance=guidance), RULE_VERIFY)
    )


def resume(inp):
    """The step's answer to a gate it raised: Verify's own, or one raised in Review's fix round."""
    return _answer(inp, os.path.join(_field(inp, "run_dir"), "verify", "report.json"))


def repair_from_review(inp, review):
    """Review asked for changes: one writer round on its findings, then Verify's checks, cases, approval."""
    artifacts = _field(inp, "artifacts")
    previous = _load(artifacts.get("verify_report"))
    ctx = _context(inp, previous=previous)
    if ctx["ledger"].rounds_left() <= 0:
        return {
            "status": "fail",
            "artifacts": {},
            "reason": "no writer round left on this ticket for the review's fix round",
            "gate": None,
            "metrics": {},
        }
    _restore(ctx, artifacts)
    findings = "\n".join(
        f"{f.get('file')}:{f.get('line')} {f.get('severity')} {f.get('summary')}: {f.get('failure_scenario')}"
        for f in (review or {}).get("findings") or []
    )
    return _guarded(
        ctx, lambda: _finish(ctx, _attempt(ctx, "review_fix", findings=findings), RULE_REVIEW_FIX)
    )


def run(inp):
    run_dir = _field(inp, "run_dir")
    report_path = os.path.join(run_dir, "verify", "report.json")
    if "answer" in _field(inp, "artifacts") and os.path.exists(report_path):
        return resume(inp)
    ctx = _context(inp)
    return _guarded(ctx, lambda: _finish(ctx, _attempt(ctx, "write"), RULE_VERIFY))
