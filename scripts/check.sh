#!/usr/bin/env bash
# The one definition of green: `just check` and the pre-push hook both run this file. It grows
# with the code. Git hooks export GIT_DIR and friends; clear them so nothing here acts on the
# hooked repository by accident.
set -uo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_PREFIX GIT_COMMON_DIR
cd "$(dirname "$0")/.."

fail=0
ok()  { printf 'ok    %s\n' "$*"; }
bad() { printf 'FAIL  %s\n' "$*"; fail=1; }

# Every shell script parses.
n=0
while IFS= read -r f; do
  head -1 "$f" | grep -q -E '^#!.*\b(ba)?sh\b' || continue
  n=$((n + 1))
  bash -n "$f" || bad "shell syntax: $f"
done < <(git ls-files scripts hooks)
ok "shell syntax ($n scripts)"

# Nothing under .local/ is tracked.
if [ -n "$(git ls-files .local)" ]; then bad ".local/ has tracked files"; else ok ".local/ untracked"; fi

# The factory's own code: lint and its tests.
if uv run --no-sync ruff check factory tests targets >/dev/null 2>&1; then ok "ruff check"; else bad "ruff check"; uv run --no-sync ruff check factory tests targets | tail -20; fi
if uv run --no-sync ruff format --check factory tests targets >/dev/null 2>&1; then ok "ruff format"; else bad "ruff format"; fi
if out=$(uv run --no-sync pytest 2>&1); then ok "pytest: $(echo "$out" | tail -1)"; else bad "pytest"; echo "$out" | tail -30; fi

if [ "$fail" -eq 0 ]; then echo "check: green"; else echo "check: red"; fi
exit "$fail"
