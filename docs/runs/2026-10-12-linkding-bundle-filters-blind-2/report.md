# linkding-bundle-filters-blind-2: Filter bundles by reading or sharing state

QA mode: blind. Steps: frame pass; plan pass; implement pass; verify pass; review pass; ship pass.

## Tests

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| bookmarks/tests/test_bundle_filters_blind_2_api.py | BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_combines_unread_shared_search_and_tags | API | pass | fails on the old code: proves the change | Lists differ: [1, 2, 3, 4] != [1] |
| bookmarks/tests/test_bundle_filters_blind_2_api.py | BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_shared_yes_no_off | API | pass | fails on the old code: proves the change | Lists differ: [1, 2, 3, 4, 5] != [1, 2, 3] |
| bookmarks/tests/test_bundle_filters_blind_2_api.py | BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_unread_yes_no_off | API | pass | fails on the old code: proves the change | Lists differ: [1, 2, 3, 4, 5] != [1, 2, 3] |
| bookmarks/tests/test_bundle_filters_blind_2_api.py | BundleReadingSharingFiltersApiTestCase::test_create_and_get_bundle_with_filter_unread_and_filter_shared | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Unread unshared', 'search': 'python', 'any_tags': '' |
| bookmarks/tests/test_bundle_filters_blind_2_api.py | BundleReadingSharingFiltersApiTestCase::test_patch_bundle_changes_filter_fields_and_keeps_others | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Patched bundle', 'search': 'python', 'any_tags': 'pr |
| bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py | BundleReadingSharingStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state | browser | pass | fails on the old code: proves the change | Locator expected to be visible |
| bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py | BundleReadingSharingStateE2ETestCase::test_edit_bundle_reading_and_sharing_state | browser | pass | fails on the old code: proves the change | Locator expected to be visible |

Counts (round 1):

| count | value |
|---|---|
| tests | 7 |
| tests_api | 5 |
| tests_browser | 2 |
| pass_at_head | 7 |
| fail_at_base_on_assertion | 7 |
| pass_on_both | 0 |
| missing_name | 0 |
| crash | 0 |
| head_fails | 0 |

## Readable test cases

| case | title | link |
|---|---|---|
| bookmarks/TC-bookmarks-001.md | TC-bookmarks-001: A bundle created through the API stores its reading and sharing state, and both default to off | [TC-bookmarks-001.md](testcases/TC-bookmarks-001.md) |
| bookmarks/TC-bookmarks-002.md | TC-bookmarks-002: PATCH on a bundle changes its reading and sharing state and leaves its other conditions alone | [TC-bookmarks-002.md](testcases/TC-bookmarks-002.md) |
| bookmarks/TC-bookmarks-003.md | TC-bookmarks-003: A bundle's reading state limits its bookmarks to unread, to read, or to both | [TC-bookmarks-003.md](testcases/TC-bookmarks-003.md) |
| bookmarks/TC-bookmarks-004.md | TC-bookmarks-004: A bundle's sharing state limits its bookmarks to shared, to unshared, or to both | [TC-bookmarks-004.md](testcases/TC-bookmarks-004.md) |
| bookmarks/TC-bookmarks-005.md | TC-bookmarks-005: Reading state, sharing state, search and tag conditions of a bundle all apply together | [TC-bookmarks-005.md](testcases/TC-bookmarks-005.md) |
| bookmarks/TC-bookmarks-006.md | TC-bookmarks-006: The new-bundle form offers reading and sharing state, previews the matches and saves the choice | [TC-bookmarks-006.md](testcases/TC-bookmarks-006.md) |
| bookmarks/TC-bookmarks-007.md | TC-bookmarks-007: The edit-bundle form changes reading and sharing state, previews the matches and saves the choice | [TC-bookmarks-007.md](testcases/TC-bookmarks-007.md) |

## Mutation

| set | checked | killed | score | changed lines checked | killed | score |
|---|---|---|---|---|---|---|
| generated | 82 | 51 | 0.622 | 16 | 16 | 1.0 |
| generated_and_developers | 82 | 77 | 0.939 | 16 | 16 | 1.0 |
| developers | 82 | 77 | 0.939 | 16 | 16 | 1.0 |

### Surviving mutants

#### generated: 31 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__filter_bundle__mutmut_6 | 183 | no |
| bookmarks.queries.x__filter_bundle__mutmut_7 | 182 | no |
| bookmarks.queries.x__filter_bundle__mutmut_16 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_17 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_18 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_19 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_20 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_21 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_22 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_23 | 191 | no |
| bookmarks.queries.x__filter_bundle__mutmut_24 | 193 | no |
| bookmarks.queries.x__filter_bundle__mutmut_25 | 193 | no |
| bookmarks.queries.x__filter_bundle__mutmut_26 | 193 | no |
| bookmarks.queries.x__filter_bundle__mutmut_27 | 195 | no |
| bookmarks.queries.x__filter_bundle__mutmut_28 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_29 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_30 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_31 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_32 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_33 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_34 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_35 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_36 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_39 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_41 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_42 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_47 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_49 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_50 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_54 | 209 | no |

1 more surviving mutants not on changed lines were left out.

#### generated_and_developers: 5 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__filter_bundle__mutmut_17 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_21 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_22 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_39 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_47 | 205 | no |

#### developers: 5 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__filter_bundle__mutmut_17 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_21 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_22 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_39 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_47 | 205 | no |

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
| spent (USD) | 5.3395 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | pass | 14.143 | - | 0.0441 | claude-sonnet-5-5 |
| plan | pass | 12.926 | - | 0.0515 | claude-sonnet-5-5 |
| implement | pass | 0.065 | - | - | - |
| verify | pass | 0.002 | 967.9 | 4.9392 | - |
| review | pass | 81.76 | - | 0.4003 | claude-opus-5-5 |
| ship | pass | 30.77 | - | - | - |

Total spend: 5.4351 USD (measured, from the run's records).
