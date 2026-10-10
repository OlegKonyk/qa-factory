| number | linkding-sort-by-modified | linkding-sort-by-modified-blind | linkding-bundle-filters-blind |
|---|---|---|---|
| qa_mode | sequential | blind | blind |
| first_round (round number) | 1 | 1 | 1 |
| first_round tests | 6 | 4 | 13 |
| first_round tests_api | 4 | 3 | 11 |
| first_round tests_browser | 2 | 1 | 2 |
| first_round pass_at_head | 6 | 4 | 13 |
| first_round fail_at_base_on_assertion | 5 | 3 | 0 |
| first_round pass_on_both | 1 | 1 | 0 |
| first_round missing_name | 0 | 0 | 13 |
| first_round crash | 0 | 0 | 0 |
| first_round head_fails | 0 | 0 | 0 |
| first_round mutation generated checked | 108 | 108 | - |
| first_round mutation generated killed | 27 | 27 | - |
| first_round mutation generated score | 0.25 | 0.25 | - |
| first_round mutation generated changed lines checked | 10 | 10 | - |
| first_round mutation generated changed lines killed | 10 | 10 | - |
| first_round mutation generated changed lines score | 1.0 | 1.0 | - |
| first_round mutation generated_and_developers checked | 108 | 108 | - |
| first_round mutation generated_and_developers killed | 98 | 98 | - |
| first_round mutation generated_and_developers score | 0.9074 | 0.9074 | - |
| first_round mutation generated_and_developers changed lines checked | 10 | 10 | - |
| first_round mutation generated_and_developers changed lines killed | 10 | 10 | - |
| first_round mutation generated_and_developers changed lines score | 1.0 | 1.0 | - |
| first_round mutation developers checked | - | 108 | - |
| first_round mutation developers killed | - | 98 | - |
| first_round mutation developers score | - | 0.9074 | - |
| first_round mutation developers changed lines checked | - | 10 | - |
| first_round mutation developers changed lines killed | - | 10 | - |
| first_round mutation developers changed lines score | - | 1.0 | - |
| final_round (round number) | 1 | 1 | 3 |
| final_round tests | 6 | 4 | 13 |
| final_round tests_api | 4 | 3 | 11 |
| final_round tests_browser | 2 | 1 | 2 |
| final_round pass_at_head | 6 | 4 | 13 |
| final_round fail_at_base_on_assertion | 5 | 3 | 12 |
| final_round pass_on_both | 1 | 1 | 1 |
| final_round missing_name | 0 | 0 | 0 |
| final_round crash | 0 | 0 | 0 |
| final_round head_fails | 0 | 0 | 0 |
| final_round mutation generated checked | 108 | 108 | 82 |
| final_round mutation generated killed | 27 | 27 | 64 |
| final_round mutation generated score | 0.25 | 0.25 | 0.7805 |
| final_round mutation generated changed lines checked | 10 | 10 | 16 |
| final_round mutation generated changed lines killed | 10 | 10 | 16 |
| final_round mutation generated changed lines score | 1.0 | 1.0 | 1.0 |
| final_round mutation generated_and_developers checked | 108 | 108 | 82 |
| final_round mutation generated_and_developers killed | 98 | 98 | 77 |
| final_round mutation generated_and_developers score | 0.9074 | 0.9074 | 0.939 |
| final_round mutation generated_and_developers changed lines checked | 10 | 10 | 16 |
| final_round mutation generated_and_developers changed lines killed | 10 | 10 | 16 |
| final_round mutation generated_and_developers changed lines score | 1.0 | 1.0 | 1.0 |
| final_round mutation developers checked | - | 108 | 82 |
| final_round mutation developers killed | - | 98 | 77 |
| final_round mutation developers score | - | 0.9074 | 0.939 |
| final_round mutation developers changed lines checked | - | 10 | 16 |
| final_round mutation developers changed lines killed | - | 10 | 16 |
| final_round mutation developers changed lines score | - | 1.0 | 1.0 |
| spend_usd | 5.4695 | 5.4826 | 8.4729 |

### linkding-sort-by-modified: stages

| step | status | duration_s | checks_s | cost_usd | model |
|---|---|---|---|---|---|
| frame | pass | 13.264 | - | 0.0308 | claude-sonnet-5-5 |
| plan | pass | 13.942 | - | 0.0669 | claude-sonnet-5-5 |
| implement | pass | 0.058 | - | - | - |
| verify | pass | 0.001 | 799.8 | 4.9005 | - |
| review | pass | 50.712 | - | 0.4714 | claude-opus-5-5 |
| ship | pass | 31.56 | - | - | - |

### linkding-sort-by-modified: rounds

| round | kind | failure |
|---|---|---|
| 1 | write | - |

Decisions: -

### linkding-sort-by-modified-blind: stages

| step | status | duration_s | checks_s | cost_usd | model |
|---|---|---|---|---|---|
| frame | pass | 11.709 | - | 0.1343 | claude-sonnet-5-5 |
| plan | pass | 14.87 | - | 0.1698 | claude-sonnet-5-5 |
| implement | pass | 0.045 | - | - | - |
| verify | pass | 817.533 | 817.4 | 4.625 | - |
| review | pass | 57.725 | - | 0.5535 | claude-opus-5-5 |
| ship | pass | 26.726 | - | - | - |

### linkding-sort-by-modified-blind: rounds

| round | kind | failure |
|---|---|---|
| 1 | write | - |

Decisions: -

### linkding-bundle-filters-blind: stages

| step | status | duration_s | checks_s | cost_usd | model |
|---|---|---|---|---|---|
| frame | pass | 14.767 | - | 0.0643 | claude-sonnet-5-5 |
| plan | pass | 12.675 | - | 0.0623 | claude-sonnet-5-5 |
| implement | pass | 0.051 | - | - | - |
| verify | fail | 312.082 | 120.1 | 0 | - |

### linkding-bundle-filters-blind: rounds

| round | kind | failure |
|---|---|---|
| 1 | write | revert: revert check: missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmark_list_page_bundle_applies_unread_and_shared_conditions; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_combines_states_with_search_and_tags; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_shared_yes_no_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_unread_yes_no_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_without_states_matches_all_states; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_create_and_get_bundle_returns_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_create_bundle_without_states_defaults_to_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_patch_bundle_changes_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_put_bundle_sets_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateFormTestCase::test_edit_bundle_form_stores_reading_and_sharing_state; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateFormTestCase::test_new_bundle_form_shows_and_stores_reading_and_sharing_state; missing-name: bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py::BundleFilterStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state; missing-name: bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py::BundleFilterStateE2ETestCase::test_edit_bundle_reading_and_sharing_state |
| 2 | repair | write_tests: test writer touched application code (reverted): ['package-lock.json'] |
| 3 | recheck | - |

Decisions: cannot_decide
