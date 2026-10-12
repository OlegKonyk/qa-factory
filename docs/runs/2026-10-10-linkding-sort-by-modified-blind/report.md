# linkding-sort-by-modified-blind: Add sort by modification date option

QA mode: blind. Steps: frame pass; plan pass; implement pass; verify pass; review pass; ship pass.

## Tests

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| bookmarks/tests/test_sort_by_modified_blind_api.py | SortByModifiedApiTestCase::test_list_archived_bookmarks_sort_modified_asc_and_desc | API | pass | fails on the old code: proves the change | Lists differ: [3, 2, 1] != [2, 1, 3] |
| bookmarks/tests/test_sort_by_modified_blind_api.py | SortByModifiedApiTestCase::test_list_bookmarks_sort_modified_asc_and_desc | API | pass | fails on the old code: proves the change | Lists differ: [3, 2, 1] != [2, 1, 3] |
| bookmarks/tests/test_sort_by_modified_blind_api.py | SortByModifiedApiTestCase::test_list_bookmarks_unknown_sort_falls_back_to_added_desc | API | pass | passes on the old code too: proves nothing | - |
| bookmarks/tests_e2e/e2e_test_sort_by_modified_blind.py | SortByModifiedE2ETestCase::test_sort_dropdown_modified_options_reorder_list | browser | pass | fails on the old code: proves the change | Locator expected to have count '1' |

Counts (round 1):

| count | value |
|---|---|
| tests | 4 |
| tests_api | 3 |
| tests_browser | 1 |
| pass_at_head | 4 |
| fail_at_base_on_assertion | 3 |
| pass_on_both | 1 |
| missing_name | 0 |
| crash | 0 |
| head_fails | 0 |

## Readable test cases

| case | title | link |
|---|---|---|
| bookmarks/TC-bookmarks-001.md | TC-bookmarks-001: The bookmarks API sorts a user's bookmarks by modification date, ascending and descending | [TC-bookmarks-001.md](testcases/TC-bookmarks-001.md) |
| bookmarks/TC-bookmarks-002.md | TC-bookmarks-002: The archived bookmarks API sorts archived bookmarks by modification date, ascending and descending | [TC-bookmarks-002.md](testcases/TC-bookmarks-002.md) |
| bookmarks/TC-bookmarks-003.md | TC-bookmarks-003: An unknown sort value in the bookmarks API falls back to newest added first | [TC-bookmarks-003.md](testcases/TC-bookmarks-003.md) |
| bookmarks/TC-bookmarks-004.md | TC-bookmarks-004: The sort dropdown offers Modified ↑ and Modified ↓ and choosing one reorders the bookmark list | [TC-bookmarks-004.md](testcases/TC-bookmarks-004.md) |

## Mutation

| set | checked | killed | score | changed lines checked | killed | score |
|---|---|---|---|---|---|---|
| generated | 108 | 27 | 0.25 | 10 | 10 | 1.0 |
| generated_and_developers | 108 | 98 | 0.9074 | 10 | 10 | 1.0 |
| developers | 108 | 98 | 0.9074 | 10 | 10 | 1.0 |

### Surviving mutants

#### generated: 81 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__base_bookmarks_query__mutmut_4 | 241 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_5 | 242 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_6 | 242 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_7 | 247 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_8 | 248 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_9 | 248 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_10 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_11 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_12 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_13 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_14 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_15 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_16 | 252 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_19 | 254 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_20 | 254 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_25 | 258 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_26 | 258 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_27 | 258 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_28 | 259 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_29 | 260 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_30 | 260 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_31 | 260 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_33 | 264 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_34 | 264 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_35 | 264 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_36 | 265 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_37 | 266 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_38 | 266 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_39 | 266 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_40 | 270 | no |

51 more surviving mutants not on changed lines were left out.

#### generated_and_developers: 10 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__base_bookmarks_query__mutmut_52 | 283 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_55 | 283 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_73 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_74 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_75 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_76 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_77 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_78 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_79 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_80 | 291 | no |

#### developers: 10 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__base_bookmarks_query__mutmut_52 | 283 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_55 | 283 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_73 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_74 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_75 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_76 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_77 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_78 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_79 | 291 | no |
| bookmarks.queries.x__base_bookmarks_query__mutmut_80 | 291 | no |

## Rounds

| round | kind | failure |
|---|---|---|
| 1 | write | - |

Stronger model's decisions: -

| ledger | value |
|---|---|
| caps | writer_rounds 3, advice 2, usd 8.0 |
| writer rounds used | 0 |
| stronger-model calls used | 0 |
| model calls in the ledger | 3 |
| spent (USD) | 5.1785 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | pass | 11.709 | - | 0.1343 | claude-sonnet-5-5 |
| plan | pass | 14.87 | - | 0.1698 | claude-sonnet-5-5 |
| implement | pass | 0.045 | - | - | - |
| verify | pass | 817.533 | 817.4 | 4.625 | - |
| review | pass | 57.725 | - | 0.5535 | claude-opus-5-5 |
| ship | pass | 26.726 | - | - | - |

Total spend: 5.4826 USD (measured, from the run's records).
