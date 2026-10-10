| number | linkding-bundle-filters-blind |
|---|---|
| qa_mode | blind |
| first_round (round number) | 1 |
| first_round tests | 13 |
| first_round tests_api | 11 |
| first_round tests_browser | 2 |
| first_round pass_at_head | 13 |
| first_round fail_at_base_on_assertion | 0 |
| first_round pass_on_both | 0 |
| first_round missing_name | 13 |
| first_round crash | 0 |
| first_round head_fails | 0 |
| final_round (round number) | 3 |
| final_round tests | 13 |
| final_round tests_api | 11 |
| final_round tests_browser | 2 |
| final_round pass_at_head | 13 |
| final_round fail_at_base_on_assertion | 12 |
| final_round pass_on_both | 1 |
| final_round missing_name | 0 |
| final_round crash | 0 |
| final_round head_fails | 0 |
| final_round mutation generated checked | 82 |
| final_round mutation generated killed | 64 |
| final_round mutation generated score | 0.7805 |
| final_round mutation generated changed lines checked | 16 |
| final_round mutation generated changed lines killed | 16 |
| final_round mutation generated changed lines score | 1.0 |
| final_round mutation generated_and_developers checked | 82 |
| final_round mutation generated_and_developers killed | 77 |
| final_round mutation generated_and_developers score | 0.939 |
| final_round mutation generated_and_developers changed lines checked | 16 |
| final_round mutation generated_and_developers changed lines killed | 16 |
| final_round mutation generated_and_developers changed lines score | 1.0 |
| final_round mutation developers checked | 82 |
| final_round mutation developers killed | 77 |
| final_round mutation developers score | 0.939 |
| final_round mutation developers changed lines checked | 16 |
| final_round mutation developers changed lines killed | 16 |
| final_round mutation developers changed lines score | 1.0 |
| spend_usd | 8.4729 |

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
