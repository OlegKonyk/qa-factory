# Common contract for every slice

Repository: /Users/oleg/dev/qa-factory, branch `feat/first-path` (already checked out). Read its
CLAUDE.md first; its rules bind you. Python 3.13 through `uv run` (already synced). Everything under
`factory/` is standard-library only at runtime. Tests go in `tests/` and run with `uv run pytest`.
Lint: `uv run ruff check factory tests targets` and `uv run ruff format factory tests targets`.

Hard rules:
- No git commands that change state (no add, commit, checkout, stash). Reading with git is fine.
- Touch only the files your slice names. Other slices run in parallel on the same tree.
- Never write under ~/Library/Caches/assay (the old lab, read-only). The factory's own linkding
  clone is at ~/Library/Caches/qa-factory/linkding: `repo` (v1.47.0), `wt/base` (commit 0837b51),
  `wt/head` (commit 0490013), venv `repo/.venv` (Python 3.13.15, pytest 9, pytest-django,
  playwright 1.62, mutmut 3.8.0, ruff). You may read them and run read-only commands against them.
  Do not modify those worktrees.
- Unit tests use small fixtures under tmp_path and the factory's own interpreter (sys.executable).
  A test that needs the real linkding clone is marked `@pytest.mark.linkding` and skips when the
  clone is absent; keep those few and fast, or gate slow ones on env `QA_FACTORY_SLOW=1`.
- Plain English in docstrings and messages. No coined vocabulary. Label numbers measured/estimated.
- Nothing that identifies Oleg's employer goes in any file (none of this work touches it; stay generic).

Definition of done for every slice: the files exist, `uv run pytest tests/<your test files>` passes,
`uv run ruff check` and `uv run ruff format --check` are clean on your files. Report DONE with the
exact commands and their full output pasted, plus a list of files written. If the spec is ambiguous,
stop and report the question instead of guessing.

Shared data shapes (dicts; only slice A defines the dataclasses, other slices never import them):

StepInput: {"ticket": dict, "repo": {"app": <app recipe dict>, "base": sha, "head": sha,
            "base_tree": path, "head_tree": path}, "artifacts": {name: path}, "round": int,
            "run_dir": path}
StepOutput: {"status": "pass"|"fail"|"needs_person", "artifacts": {name: path}, "reason": str,
             "gate": {"who","question","context"} | None, "metrics": dict}

App recipe (targets/linkding/app.json), paths may start with `~`:
{"name": "linkding",
 "repo": "~/Library/Caches/qa-factory/linkding/repo",
 "worktrees": "~/Library/Caches/qa-factory/linkding/wt",
 "python": "~/Library/Caches/qa-factory/linkding/repo/.venv/bin/python",
 "source_package": "bookmarks",
 "pytest_args": ["-p", "no:cacheprovider"],
 "api_tests_dir": "bookmarks/tests",
 "browser_tests_dir": "bookmarks/tests_e2e",
 "browser_test_files": "e2e_test_*.py",
 "test_support": ["bookmarks/tests/helpers.py", "bookmarks/tests_e2e/helpers.py"],
 "exclude_copy": [".git", "node_modules", ".venv", "mutants", "__pycache__", ".pytest_cache"],
 "mutmut": {"pytest_add_cli_args": ["-p", "no:cacheprovider", "-o", "django_find_project=false"],
            "pre_create_dirs": ["data/assets", "data/favicons", "data/previews"]},
 "suite": [["-n", "auto", "bookmarks/tests"],
           ["-o", "python_files=e2e_test_*.py", "bookmarks/tests_e2e"]],
 "strategy": "targets/linkding/strategy.md"}

Ticket (targets/linkding/tickets/sort-by-modified.json):
{"id": "linkding-sort-by-modified", "app": "targets/linkding/app.json",
 "base": "0837b5186979e4a52e75582bd295cc73e43d2612", "head": "0490013e4f67f0d31ccd764a5cb723dcafaf4acd",
 "title": "...", "description": "...", "acceptance_criteria": ["..."]}

Run folder: `.artifacts/runs/<ticket id>/` holding `ticket.json`, `steps/NN-<name>.json` (one record
per step), `question.md` and `answer.json` at the gate, and each step's artifacts in a subfolder named
after the step.
