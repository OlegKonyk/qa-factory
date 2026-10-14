# linkding-sort-by-modified-vague: Add sort by modification date option

QA mode: blind. Steps: frame needs_person: Frame cannot hand 'Add sort by modification date option' to a test writer as is: - missing from the ticket: AC3: the DOM locator of the sort dropdown on the bookmark list page is not stated by the ticket or the code before the change. The code renders a form field from BookmarkSearchForm.sort in search.html, but the select's id/name in the rendered page is not given, and neither is whether the option value attribute equals 'modified_asc'/'modified_desc'. - missing from the ticket: AC3: the URL query behaviour after selecting an option (whether the page reloads with ?sort=modified_asc) is not stated. - missing from the ticket: AC4: the route for the archived UI list page is not named in the ticket. It is only implied by 'archived bookmarks list'. - missing from the ticket: AC1/AC2: the way to set distinct date_modified values for fixtures is not stated. The ticket does not say whether the API response exposes a date_modified field to assert on, so tests may need to check order by bookmark IDs or titles.; plan not run; implement not run; verify not run; review not run; ship not run.

## Tests

No revert report in the final round.

Counts (round 1):

| count | value |
|---|---|
| tests | - |
| tests_api | - |
| tests_browser | - |
| pass_at_head | - |
| fail_at_base_on_assertion | - |
| pass_on_both | - |
| missing_name | - |
| crash | - |
| head_fails | - |

## The developers' own tests, written with the change

Not run for this ticket (`python -m factory devtests <run folder>` runs it afterwards).

## Readable test cases

No readable cases were written.

## Mutation

No mutation numbers in the final round.

### Surviving mutants
No mutation report in the final round.

## Rounds

| round | kind | failure |
|---|---|---|
| 1 | write | - |

Stronger model's decisions: -

Ledger: -

## Who answered

| step | round | by | decision | note | answered at |
|---|---|---|---|---|---|
| frame | 1 | Oleg (the session, standing in for the proof run) | clarify | the contract from the original ticket | 2026-10-14T12:52:54+00:00 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | needs_person | 21.245 | - | 0.0563 | claude-sonnet-5-5 |

Total spend: 0.0563 USD (measured, from the run's records).
