# linkding-bundle-filters-blind: Filter bundles by reading or sharing state

QA mode: blind. Steps: frame pass; plan pass; implement pass; verify fail: spend cap reached: 8.35 of 8.00 USD spent on this ticket; review not run; ship not run.

## Tests

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_bookmark_list_page_bundle_applies_unread_and_shared_conditions | API | pass | fails on the old code: proves the change | unexpectedly None |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_bookmarks_api_bundle_combines_states_with_search_and_tags | API | pass | fails on the old code: proves the change | Items in the first set but not the second: |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_shared_yes_no_off | API | pass | fails on the old code: proves the change | Items in the first set but not the second: |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_unread_yes_no_off | API | pass | fails on the old code: proves the change | Items in the first set but not the second: |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_bookmarks_api_bundle_without_states_matches_all_states | API | pass | passes on the old code too: proves nothing | - |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_create_and_get_bundle_returns_filter_unread_and_filter_shared | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Bundle with states', 'search': 'foo', 'any_tags': '' |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_create_bundle_without_states_defaults_to_off | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Bundle without states', 'search': '', 'any_tags': '' |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_patch_bundle_changes_filter_unread_and_filter_shared | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Existing bundle', 'search': 'foo', 'any_tags': '', ' |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateApiTestCase::test_put_bundle_sets_filter_unread_and_filter_shared | API | pass | fails on the old code: proves the change | 'filter_unread' not found in {'id': 1, 'name': 'Updated bundle', 'search': 'bar', 'any_tags': '', 'a |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateFormTestCase::test_edit_bundle_form_stores_reading_and_sharing_state | API | pass | fails on the old code: proves the change | 0 != 1 : No single label 'Reading State' found |
| bookmarks/tests/test_bundle_filters_blind_api.py | BundleFilterStateFormTestCase::test_new_bundle_form_shows_and_stores_reading_and_sharing_state | API | pass | fails on the old code: proves the change | 0 != 1 : No single label 'Reading State' found |
| bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py | BundleFilterStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state | browser | pass | fails on the old code: proves the change | Locator expected to be visible |
| bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py | BundleFilterStateE2ETestCase::test_edit_bundle_reading_and_sharing_state | browser | pass | fails on the old code: proves the change | Locator expected to be visible |

Counts (round 3):

| count | value |
|---|---|
| tests | 13 |
| tests_api | 11 |
| tests_browser | 2 |
| pass_at_head | 13 |
| fail_at_base_on_assertion | 12 |
| pass_on_both | 1 |
| missing_name | 0 |
| crash | 0 |
| head_fails | 0 |

## Readable test cases

No readable cases were written. Verify ended with: spend cap reached: 8.35 of 8.00 USD spent on this ticket

## Mutation

| set | checked | killed | score | changed lines checked | killed | score |
|---|---|---|---|---|---|---|
| generated | 82 | 64 | 0.7805 | 16 | 16 | 1.0 |
| generated_and_developers | 82 | 77 | 0.939 | 16 | 16 | 1.0 |
| developers | 82 | 77 | 0.939 | 16 | 16 | 1.0 |

### Surviving mutants

#### generated: 18 survived

| mutant | source line | on a changed line |
|---|---|---|
| bookmarks.queries.x__filter_bundle__mutmut_6 | 183 | no |
| bookmarks.queries.x__filter_bundle__mutmut_7 | 182 | no |
| bookmarks.queries.x__filter_bundle__mutmut_16 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_17 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_18 | 189 | no |
| bookmarks.queries.x__filter_bundle__mutmut_21 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_22 | 190 | no |
| bookmarks.queries.x__filter_bundle__mutmut_24 | 193 | no |
| bookmarks.queries.x__filter_bundle__mutmut_32 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_33 | 196 | no |
| bookmarks.queries.x__filter_bundle__mutmut_39 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_41 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_42 | 200 | no |
| bookmarks.queries.x__filter_bundle__mutmut_47 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_49 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_50 | 205 | no |
| bookmarks.queries.x__filter_bundle__mutmut_54 | 209 | no |
| bookmarks.queries.x__filter_bundle__mutmut_55 | 209 | no |

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
| 1 | write | revert: revert check: missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmark_list_page_bundle_applies_unread_and_shared_conditions; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bu ... |
| 2 | repair | write_tests: test writer touched application code (reverted): ['package-lock.json'] |
| 3 | recheck | - |

Stronger model's decisions: cannot_decide

| ledger | value |
|---|---|
| caps | writer_rounds 3, advice 2, usd 8.0 |
| writer rounds used | 1 |
| stronger-model calls used | 1 |
| model calls in the ledger | 3 |
| spent (USD) | 8.3463 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | pass | 14.767 | - | 0.0643 | claude-sonnet-5-5 |
| plan | pass | 12.675 | - | 0.0623 | claude-sonnet-5-5 |
| implement | pass | 0.051 | - | - | - |
| verify | fail | 312.082 | 120.1 | 0 | - |

Total spend: 8.4729 USD (measured, from the run's records).
