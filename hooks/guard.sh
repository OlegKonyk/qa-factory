#!/usr/bin/env bash
# Keeps employer-identifying terms out of this repository.
# The terms live only in a local, untracked file, one per line, matched
# case-insensitively. They are never written into this repository.
#   guard.sh staged           scan the lines and file names being committed
#   guard.sh message <file>   scan a commit message
set -u
LIST="${QA_FACTORY_BLOCKLIST:-$HOME/.config/konyklabs/blocklist.txt}"

if [ ! -s "$LIST" ]; then
  echo "WARN: $LIST is missing or empty, so the term scan was skipped" >&2
  exit 0
fi

# A blank line in the list would match everything, and stray whitespace or a
# carriage return would stop a term matching, so normalise the list first.
terms=$(mktemp)
trap 'rm -f "$terms"' EXIT
sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d' "$LIST" > "$terms"
if [ ! -s "$terms" ]; then
  echo "WARN: $LIST holds no terms, so the term scan was skipped" >&2
  exit 0
fi

case "${1:-}" in
  staged)
    # Added lines only, so removing a term is never blocked. File names are
    # listed separately because a binary file has no added lines to carry one.
    hits=$({ git diff --cached -U0 --no-color | grep '^+'; git diff --cached --name-only; } \
      | grep -n -i -f "$terms" | head -10)
    what="staged changes"
    ;;
  message)
    hits=$(grep -n -i -f "$terms" "${2:?message file}" | head -10)
    what="the commit message"
    ;;
  *)
    echo "usage: guard.sh staged | guard.sh message <file>" >&2
    exit 2
    ;;
esac

if [ -n "$hits" ]; then
  echo "BLOCKED: a term from $LIST appears in $what:" >&2
  echo "$hits" >&2
  echo "Replace it with the generic description, or move the material to .local/." >&2
  exit 1
fi
exit 0
