# s2 · Files mutmut's working tree needs: `mutmut.also_copy`

Branch `fix/mutmut-also-copy`, worktree `~/dev/qa-factory-wt/alsocopy`. Written 2026-10-14 from the
first gafaelfawr run (`.artifacts/runs/gafaelfawr-oidc-client-updates`, round 1).

## The defect, measured

mutmut 3.8.0 copies only `source_paths` and the tests into `mutants/` and runs pytest there. The
first run's `mutants/` held `pyproject.toml`, `src`, `tests`, `uv.lock` and nothing else.
gafaelfawr's `tests/conftest.py` fixture `empty_database` calls safir's `stamp_database_async`,
which reads `alembic.ini` and the `alembic/` folder from the current directory; in `mutants/`
they do not exist, alembic raised `CommandError`, pytest reported `1 error`, mutmut printed
`failed to collect stats. runner returned 1` and exited 1 with 534 mutants generated and 0
checked. The factory read that as "the generated tests never reach the changed functions"
(`repairable: true`) and spent a writer round on tests that could not fix it.

mutmut has the setting for this: `also_copy` in `[tool.mutmut]`, a list of paths copied into
`mutants/` before the run (`mutmut/configuration.py` line 184, `mutmut/utils/file_utils.py`
`copy_also_copy_files`; read, not yet measured). The factory's `pre_create_dirs` creates empty
folders there, which is not the same need.

## The change

1. **Recipe field** `mutmut.also_copy` (optional, default `[]`): paths relative to the repository
   root (files or folders) that mutmut copies into `mutants/`. Read in `factory/steps/verify.py`
   where `pre_create_dirs` is read (`app["mutmut"].get("also_copy", [])`), passed through
   `mutants.run(...)` as a new keyword `also_copy=()` to `_mutmut_config`, which emits
   `also_copy = [...]` (with `_toml_list`) when the list is not empty. `mutation_rerun.py` goes
   through `run_mutation` and needs nothing; `implement.py` reads `pre_create_dirs` for the
   worktree, not for mutmut, and needs nothing.
2. **The failure reason tells the truth.** In `factory/checks/mutants.py`, `classify_exit` (or
   wherever "mutmut checked no mutant: the generated tests never reach the changed functions"
   is produced; grep for it) must distinguish "pytest could not run in `mutants/`" from "the
   tests ran and reached nothing". The signal mutmut gives: `failed to collect stats. runner
   returned <code>` or `Failed to run clean test` in the output together with a non-zero exit
   and no mutant with an exit code (the same pair `_broke_before_checking` uses). When that is
   the case, the status is `fail` with reason `mutmut could not run the tests in its working
   tree: <last pytest error line>; check mutmut.also_copy and mutmut.pytest_add_cli_args in the
   recipe` and `repairable: false` (so Verify does not spend a writer round on it; read how
   `repairable` is consumed in `verify.py` and make the non-repairable failure stop the run the
   way an environment failure does, through the existing escalation or gate path, not a crash).
   Keep the existing reason for the case where pytest ran and the tests reached no mutant
   (mutmut exits 0 or every mutant is `no_tests`).
3. **Tests**: `_mutmut_config` emits `also_copy` when given and not otherwise; the classify
   change on a fake output with `failed to collect stats. runner returned 1` and no exit codes
   gives the new reason and `repairable: false`; the existing fake-`subprocess.run` test of
   `mutants.run` passes `also_copy=["alembic", "alembic.ini"]` and asserts the written
   `pyproject.toml` holds it; a `run_mutation` test with `mutmut: {"also_copy": [...]}` in the
   fake app passes it through (extend the existing fake-ctx tests in `tests/test_verify_loop.py`).
4. **Docs**: `docs/adopt.md` section 4 table: a row `mutmut.also_copy` ("files or folders
   relative to the repository root that the tests need beside the code when mutmut runs them in
   its `mutants/` copy, for example `["alembic", "alembic.ini"]` for a suite whose fixtures stamp
   or migrate the database; `[]` if none"), and in section 7 under the mutation verdict: the new
   reason and that it is a recipe gap, not a test failure. `docs/log.md`: a short entry with the
   measured facts above.

## Definition of done

`just check` green in the worktree, output pasted. No git commands.
