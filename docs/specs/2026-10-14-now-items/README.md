# Specs: the roadmap's "Now" group, 2026-10-14

One spec per slice. Roadmap item 2 is `s2a` to `s2c` (branch `fix/mutation-resume-devtests`),
item 4 is `s4a` and `s4b` (branch `feat/person-gates`), item 1 is `s1` (branch
`feat/deployed-run`). Each slice was implemented by an Opus agent from the spec alone and reviewed
by a second Opus agent before the session accepted it. Rules every slice follows: a factory test
for every change, `uv run --no-sync ruff check factory tests targets` and `ruff format --check`
clean, `uv run --no-sync pytest` green, no `git commit` (the session commits), evidence pasted.
