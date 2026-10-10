# Slice C: mutation testing on the changed functions, and the application's own suite

Files: factory/checks/mutants.py, factory/checks/suite.py, tests/test_mutants.py, tests/test_suite.py.

Facts measured today on linkding at commit 0490013 with mutmut 3.8.0 (keep them in a comment):
- Config lives in `[tool.mutmut]` of pyproject.toml: source_paths = ["bookmarks"],
  only_mutate = ["bookmarks/queries.py"], pytest_add_cli_args_test_selection = [test files],
  pytest_add_cli_args = ["-p", "no:cacheprovider", "-o", "django_find_project=false"],
  use_git_change_detection = false. Without `django_find_project=false`, pytest-django puts the
  original tree ahead of the mutated copy on sys.path and mutmut reports "could not find any test
  case for any mutant".
- The mutated copy lives in `mutants/`; the app's settings resolve its data dir relative to the
  copy, so `mutants/data/assets`, `mutants/data/favicons`, `mutants/data/previews` must exist
  before `mutmut run` (otherwise sqlite3 "unable to open database file").
- `mutmut run '<module>.<mangled>__mutmut_*'` limits the run to those mutants. Mangled names:
  top-level `def _base_bookmarks_query` → `bookmarks.queries.x__base_bookmarks_query__mutmut_N`
  (prefix `x_` + name); a method → `module.xǁClassǁmethod__mutmut_N` (U+01C1).
- Results: `mutants/<relpath>.meta` (note: `queries.py.meta`, the `.py` stays) is JSON with
  `exit_code_by_key` {mutant name: code}: 1 or 3 killed, 0 survived, 5 or 33 no tests, 36/-24/24/
  152/255 timeout, null not checked; anything else "other". Scoped run on `_base_bookmarks_query`
  with the developers' test_queries.py: 454 generated, 108 checked, 98 killed, 10 survived, 115 s
  wall (measured).
- The mutated module `mutants/bookmarks/queries.py` holds `def x_<f>__mutmut_orig(...)` and one
  `def x_<f>__mutmut_N(...)` per mutant, same signature, usually one line differs.

## mutants.py
`changed_functions(base_src: str | None, head_src: str, module: str) -> list[str]`: parse both
with ast; walk head's top-level FunctionDef/AsyncFunctionDef and methods of top-level classes;
a function is changed when base has no function of the same qualified name or
`ast.dump(node, include_attributes=False)` differs (so a comment-only or formatting change adds
nothing). Return mutmut globs `f"{module}.x_{name}__mutmut_*"` / `f"{module}.xǁ{Class}ǁ{name}__mutmut_*"`.
`changed_lines(base_src, head_src) -> set[int]`: 1-based head lines in difflib replace/insert
opcodes.
`mutant_lines(mutated_module_src, func_mangled) -> dict[str, int | None]`: for each
`x_<f>__mutmut_N` function in the mutated module, the 0-based offset of the first line that differs
from `x_<f>__mutmut_orig` (compare the function bodies line by line by position; difflib for
differing lengths); None when nothing differs. The caller maps offset → head line as
`orig_def_line_in_head + offset` where `orig_def_line_in_head` is the `lineno` of the original
function in the head source (provide `function_def_line(head_src, qualified_name)`).
`run(head_tree, python, source_package, only_mutate, test_files, globs, workdir, pytest_add_cli_args,
     pre_create_dirs, exclude_copy, changed_lines_by_file, timeout=1800) -> dict`:
- copy head_tree to `<workdir>/mutation` skipping exclude_copy names (shutil.copytree with ignore);
  append the `[tool.mutmut]` table to its pyproject.toml (build the TOML by hand: arrays of
  strings); mkdir `mutants/<d>` for each pre_create_dirs; run
  `[<dir of python>/mutmut, "run", *globs]` with cwd there, `stdin=DEVNULL`, capture, wall time.
- For each only_mutate relpath read `mutants/<relpath>.meta`; map codes to statuses; for each
  checked mutant compute its head line via mutant_lines + function_def_line and whether that line is
  in `changed_lines_by_file[relpath]`.
- Return {"status": "pass" | "fail", "reason", "wall_s", "returncode", "generated", "checked",
  "killed", "survived", "no_tests", "timeout", "other", "score" (killed / (killed + survived), None
  when 0 checked), "on_changed_lines": {"checked","killed","survived","score"}, "mutants":
  {name: {"status","line","changed_line"}}, "stdout_tail": last 30 lines, "tree": path}.
  "fail" only when mutmut itself failed to run (non-zero return code with no .meta, or a timeout);
  the score threshold is the caller's decision.
Mutmut's binary is `os.path.join(os.path.dirname(python), "mutmut")`.

## suite.py
`run(tree, python, invocations, pytest_args, timeout=1800) -> dict`: for each list in
`invocations` run `[python, "-m", "pytest", *pytest_args, *invocation]` with cwd=tree; record
returncode, wall_s, and the summary line (last line matching r"\d+ (passed|failed|error)").
{"status": "pass" when every returncode is 0 else "fail", "runs": [{"args","returncode",
"summary","wall_s","tail": last 20 lines}]}.

## Tests
tests/test_mutants.py: changed_functions on fixture sources (new function; changed body;
unchanged; comment-only change → absent; a method → ǁ glob; a function removed in head → absent);
changed_lines; mutant_lines on a hand-written mutated module in mutmut's layout
(`def x_f__mutmut_orig(a):\n    return a + 1\n` and `def x_f__mutmut_1(a):\n    return a - 1\n`
plus a two-line body variant where the second line differs → offset 1); function_def_line;
the meta parsing via a helper `summarize_meta(meta_dict) -> counts` on a fixture dict with every
code class. Add one `@pytest.mark.linkding` test gated also on env QA_FACTORY_SLOW=1 that runs
`run()` for real against the head worktree with only_mutate ["bookmarks/queries.py"],
test_files ["bookmarks/tests/test_queries.py"], globs from changed_functions(base, head), and
asserts checked > 0 and killed > 0. Register the markers in pyproject.toml's
`[tool.pytest.ini_options]` `markers` list (add the key; keep the existing keys).
tests/test_suite.py: fixture tree with a passing file and a failing file; invocations run each;
status fail and summaries present; passing-only → pass.
