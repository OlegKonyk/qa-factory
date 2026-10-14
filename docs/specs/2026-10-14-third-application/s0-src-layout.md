# s0 · Module names for a `src/` layout

Branch `fix/src-layout`, worktree `~/dev/qa-factory-wt/srclayout`. Written 2026-10-14 for roadmap
item 3 (a third application, which may have a `src/<package>/` layout; `docs/adopt.md` section 3
item 4 says that layout is not verified).

## The defect

mutmut 3.8.0 names every mutant by the mutated file's path with the suffix dropped, slashes to dots,
and **a leading `src.` stripped** (`mutmut/utils/format_utils.py`, `get_mutant_name`:
`strip_prefix(module_name, prefix="src.")`; also `.__init__.` collapsed). So `src/pkg/views.py`
gives keys `pkg.views.x_f__mutmut_N`.

The factory derives the module name from the path without that stripping, in three places:

1. `factory/steps/verify.py`, `run_mutation`: `mutants.changed_functions(base_src, head_src,
   path[:-3].replace("/", "."))` builds the globs mutmut is told to run (`src.pkg.views.x_f__mutmut_*`).
   With a `src/` layout no glob matches any key: mutmut reports nothing matching, and the check
   says no mutant was checked.
2. `factory/checks/mutants.py`, `_module_of(relpath)`: used to match `left_decorated` entries
   against the globs. Same derivation, same miss.
3. `factory/steps/verify.py`, the lint call: `lint.run(..., app_package=ctx["app"]["source_package"])`.
   `lint._ast_findings` compares a dotted patch target (`pkg.http.fetch`) with `app_package`; for a
   recipe whose `source_package` is `src/pkg` the comparison is against the path string, never
   matches, and the `mocks-own-code` rule silently never fires. (For `pkg` the path and the dotted
   name coincide, which is why it works today.)

## The change

In `factory/checks/mutants.py` add two small public helpers and use them everywhere a path becomes
a module name:

- `module_of(relpath: str) -> str`: the dotted module of a `.py` path as mutmut 3.8.0 keys it:
  drop `.py`, slashes to dots, strip a leading `src.` (only the first path component, only when it
  is exactly `src`), and collapse a trailing `.__init__` (so `src/pkg/__init__.py` → `pkg`,
  `pkg/sub/__init__.py` → `pkg.sub`, `pkg/a.py` → `pkg.a`, `src/pkg/a.py` → `pkg.a`,
  `source/pkg/a.py` → `source.pkg.a`: mutmut strips `src.` only, so the factory does the same,
  nothing more). Replace `_module_of` with it.
- `package_module(source_package: str) -> str`: the dotted import name of the recipe's
  `source_package` directory, same rule (`src/pkg` → `pkg`, `pkg` → `pkg`, `src/pkg/sub` →
  `pkg.sub`).

Then:

- `verify.py` `run_mutation`: `mutants.changed_functions(base_src, head_src, mutants.module_of(path))`.
  `changed_functions` keeps its own `.__init__` handling (harmless, now redundant; leave it).
- `verify.py` lint call: `app_package=mutants.package_module(ctx["app"]["source_package"])`.
- `verify.py` around line 890 compares `path[:-3].replace("/", ".") == module` (the readable cases or a per-module lookup; read it): use `mutants.module_of(path)` there too, and check what `module` on the other side of that comparison is derived from, so both sides use the same rule.
- Grep `factory/` for every other `replace("/", ".")` or equivalent path-to-module derivation and
  route it through `module_of` (`factory/checks/mutation_rerun.py` reuses `run_mutation`; check it
  needs nothing else).

Nothing else changes: `source_package` stays a path relative to the repository root everywhere it
is used as a path (`path.startswith(pkg + "/")`, mutmut's `source_paths`, the cases folder).

## Tests (pytest, in the existing files; `py-testing` conventions)

- `tests/test_mutants.py`: `module_of` for the six paths above; `package_module` for the three;
  `changed_functions(..., module_of("src/pkg/f.py"))` produces `pkg.f.x_f__mutmut_*` for a new
  function `f`, and for a method `pkg.f.xǁCǁm__mutmut_*` (use the module's `BAR` constant, do not
  retype the character).
- The `left_decorated` matching in `mutants.run` uses `module_of`: a unit test on whatever small
  seam exists (if `run` cannot be exercised without mutmut, test `module_of` and leave a one-line
  comment at the call site; do not build a harness).
- `tests/test_lint.py`: with `app_package="bookmarks"` the existing test stays; add that
  `package_module("src/bookmarks")` is `"bookmarks"` and that the verify-side call passes the
  dotted name (a test on `verify.py` only if one already exercises the lint call with a fake
  context; otherwise the helper test is enough).
- `tests/test_verify_loop.py` or wherever `run_mutation` is exercised with a fake `ctx`: one case
  with `source_package: "src/pkg"` and a changed file `src/pkg/f.py` asserting the globs in the
  report are `pkg.f.x_...`. If no such test exists, add the smallest one that drives `run_mutation`
  up to the `report["globs"]` computation (it returns early with `skipped` when there is no
  function; so give the file one changed function and stub `mutants.run` with monkeypatch to
  return a minimal dict, or assert on `report["globs"]` before the sets are run if the shape
  allows; read the function first).

## Docs, same branch

- `docs/adopt.md`: section 3 item 4: `src/` layout: the factory now names modules as mutmut does
  (a leading `src/` dropped); mark it "built 2026-10-14, not yet measured on an application"
  (the onboarding run that follows measures it); section 1 table row "A `src/` layout for the
  source package" accordingly. Say in section 4 (`source_package`) that it is the package
  directory relative to the root, `src/pkg` for a src layout, and that the factory derives the
  import name from it.
- `docs/log.md`: a short entry under today's date with the mutmut fact (file and function named)
  and what was measured: the factory tests only, nothing on an application yet.

## Definition of done

`just check` green in the worktree, output pasted. `ruff check` and `ruff format --check` clean.
No git commands: the session commits.
