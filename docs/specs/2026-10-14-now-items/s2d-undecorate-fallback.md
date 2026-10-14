# s2d · Fall back to the plain copy when the decorator rewrite breaks the import

Worktree: `~/dev/qa-factory-wt/fixes` (branch `fix/mutation-resume-devtests`), on top of s2a to
s2c (committed as bd6d271). Read `factory/checks/mutants.py` (`undecorate`, `run`) first.

## The finding (review of s2a, medium)

`undecorate` moves a method's decorator expression from class scope to module scope. A decorator
that refers to a name defined in the class body (`class Store: _lock = Lock(); @synchronized(_lock)
def put(...)`) then raises `NameError` when the mutated copy is imported; mutmut's clean run
fails and `run_mutation` raises the non-repairable "mutmut did not run", so Verify fails for a
file that got a verdict before the rewrite existed. Decorators a metaclass or class-creation hook
reads (`@abstractmethod`, pydantic's `@validator`, SQLAlchemy's `@validates`) change behaviour
the same way when applied after the class exists.

## The fix

1. **Skip what can be seen statically.** In `undecorate`, leave a method decorated when its
   decorator expression names something bound in the class body (walk the class body for
   assignments, function and class definitions, and compare the `ast.Name` ids the decorator
   uses), or when it is one of `abstractmethod`, `validator`, `field_validator`, `root_validator`,
   `model_validator`, `validates`, `declared_attr`, `hybrid_property`, `singledispatchmethod`,
   `overload` (by its last attribute or name). Record every function left decorated and why in the
   `unmutated`-style list the run already prints (`skipped: ... left decorated: <reason>`).
2. **Fall back when the import still breaks.** In `mutants.run`, when the rewritten copy's mutmut
   run fails before any mutant is checked (`classify_exit` says it did not run, or the clean run
   failed: find the signal mutmut gives, from its output or exit code, and name it in a comment),
   run once more on a copy without the rewrite, and report `"undecorate": "fallen back: <reason>"`
   in the run's result so the report shows it. Never fall back when mutmut ran and checked mutants.
3. The `no_cache_headers` case stays a known limit.

## Tests and evidence

- `tests/test_mutants.py`: a method whose decorator names a class attribute stays decorated;
  `@abstractmethod` stays decorated; the reason is listed; the fallback path with a fake mutmut
  runner that fails once with the rewrite and passes without it; no fallback after a run that
  checked mutants.
- `uv run --no-sync ruff check factory tests targets`, `ruff format --check`, `pytest`: last lines.
- Then the real run again, to show nothing regressed: `uv run --no-sync python -m factory mutation
  /Users/oleg/dev/qa-factory/.artifacts/runs/isso-no-cache-comment-views`; paste the output lines
  (it takes about 11 minutes; run it in the background and keep working on the tests).

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
