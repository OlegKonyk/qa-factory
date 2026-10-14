# s2a · Mutation where mutmut makes no mutants

Worktree: `~/dev/qa-factory-wt/fixes` (branch `fix/mutation-resume-devtests`). Work only there.
Run the factory's tools from that folder with `uv run --no-sync ...`.

## The problem, measured on 2026-10-13

isso ticket `isso-no-cache-comment-views` (run folder
`/Users/oleg/dev/qa-factory/.artifacts/runs/isso-no-cache-comment-views`, worktrees
`~/Library/Caches/qa-factory/isso/wt/isso-no-cache-comment-views/{base,head}`, head `7e91d59`,
the shipped tests committed on top as `59a58be`; the tests are also copied under the run folder's
`verify/tests/`). The change touched four functions:

- `isso/views/comments.py`: `no_cache_headers` (a new top-level decorator that defines an inner
  function), `API.view` and `API.fetch` (methods that gained the `@no_cache_headers` decorator).
- `isso/utils/__init__.py`: a new helper. The factory never mutates `__init__.py`
  (`factory/steps/verify.py`, `run_mutation`, the `endswith("/__init__.py")` filter).

mutmut 3.8.0 generated 1039 mutants for `comments.py` and none for the three functions. Its rule
(`mutmut/mutation/file_mutation.py`, around line 325, in the isso venv at
`~/Library/Caches/qa-factory/isso/repo/.venv/lib/python3.*/site-packages/mutmut/`): every
decorated function is ignored except one decorated only with `@staticmethod` or `@classmethod`,
because copying a decorated function for its trampoline can register a route twice, a decorator
runs at definition time, and `@property` breaks the trampoline. That explains `API.view` and
`API.fetch`. It does **not** explain `no_cache_headers`, which has no decorator; find out why it got
no mutant (an inner `def`? the `functools.wraps` call? something else) by reading the same file and
by running mutmut on a small copy.

## Step 1, before any factory change: measure

Run mutmut 3.8.0 by hand on a scratch copy of the isso head tree (copy it with the recipe's
`exclude_copy` list; never run mutmut inside the worktree itself) and record, for each of the
four functions, whether a mutant is generated:

1. as the code is;
2. with the candidate rewrite of step 2 applied by hand to `comments.py`;
3. for `isso/utils/__init__.py`: what key mutmut gives its mutants (`isso.utils.x_<f>__mutmut_*`,
   `isso.utils.__init__.x_<f>__mutmut_*`, or another), read from `mutants/isso/utils/__init__.py.meta`.

Use `factory.checks.mutants.run` where it fits (it writes the mutmut config and reads the meta
files) or the mutmut command line. Put the measurements in your report as a table.

## Step 2: the fix

1. **Decorated functions.** A pre-pass in `factory/checks/mutants.py`, applied to every
   `only_mutate` file in the copy mutmut mutates (not to the worktree), that turns a decorated
   function into an undecorated one plus an assignment, **keeping every existing line number**
   (the factory maps mutants to changed lines by line number):
   - each decorator line becomes a comment line (`# @dec` or `#` for a continuation line of a
     multi-line decorator), so the count of lines before the `def` is unchanged;
   - the equivalent assignment is appended at the **end of the module**: `f = dec(f)` for a
     top-level function, `Cls.meth = dec(Cls.meth)` for a method; several decorators apply
     bottom-up (`@a @b def f` becomes `f = a(b(f))`);
   - `@staticmethod` and `@classmethod` alone are left as they are (mutmut handles them);
     `@property`, `@x.setter` and other descriptor decorators on methods are left as they are
     too, with a note in the report, unless step 1 shows the rewrite works for them;
   - functions nested inside other functions are not touched.
   Use `ast` to find the decorators and their line ranges (`node.decorator_list`, `lineno`,
   `end_lineno`) and edit the text by line; do not unparse (comments and layout must stay).
   If step 1 shows a decorator whose registration order matters (a route decorator that must run
   before another statement in the module), note it as a limit; do not try to solve it.
2. **The inner-function case** (`no_cache_headers`): fix it if the measurement shows a shape the
   pre-pass or a mutmut setting can handle; otherwise record exactly why mutmut makes no mutant
   for it and leave it as a known limit in the report (`skipped` reason names the function).
3. **`__init__.py`.** `run_mutation` mutates a non-empty `__init__.py` under the source package
   like any other module; `mutants.changed_functions` builds the glob with the key mutmut uses
   (from step 1.3). Empty `__init__.py` files have no functions and fall out naturally.
4. **A command to run the mutation check again on a finished run, with no writer call:**
   `python -m factory mutation <run folder>`, modelled on `factory/checks/devtests.py`
   (`run_on_record`, `main`, the `devtests` subcommand in `factory/__main__.py`). It reads the
   Implement record and the run's `verify/tests_manifest.json`, puts the shipped tests back into
   the head tree with `factory.steps.ship.restore_tests` from `verify/tests/`, runs the same
   mutation check Verify runs (`verify.run_mutation` on a context built like `verify._context`,
   or a thin wrapper that shares its code; do not duplicate the check), writes the result to
   `<run folder>/verify/mutation-rerun.json` (never over `mutation.json`), and prints one line
   per run set (checked, killed, survived, score, on the changed lines) or the `skipped` reason.
   Exit 0 when mutmut ran or was skipped for a stated reason, 1 on an error.
5. `docs/adopt.md`: section 5 ("Choosing the commit") and section 7 ("Mutation not applicable")
   describe the old limits; rewrite those sentences to the new behaviour, and add the command to
   section 7 beside `devtests`.

## Step 3: tests and evidence

- Factory tests (`tests/test_mutants.py`, a new `tests/test_mutation_command.py`): the pre-pass
  on source text (a decorated top-level function, a decorated method, two decorators, a multi-line
  decorator, `@staticmethod` untouched, a nested function untouched; every case asserts the line
  count and the position of every unchanged line), the `__init__.py` glob, and the command with a
  fake `mutants.run` (no mutmut), including the exit codes.
- `uv run --no-sync ruff check factory tests targets`, `uv run --no-sync ruff format --check
  factory tests targets`, `uv run --no-sync pytest`: paste the last lines.
- **The real run:** `uv run --no-sync python -m factory mutation
  /Users/oleg/dev/qa-factory/.artifacts/runs/isso-no-cache-comment-views`. Paste the whole output
  and the wall time. Done when it reports mutants checked for the changed code (at least the two
  methods and the `__init__.py` helper), with the generated tests' kills on the changed lines.
  If one of the four functions still gets no mutant, say which and why.

## Report

Files changed; the measurement table of step 1; the commands and their output; deviations from
this spec with the reason; what was left alone. Do not commit.
