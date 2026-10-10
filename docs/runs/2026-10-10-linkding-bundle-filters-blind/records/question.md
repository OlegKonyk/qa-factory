# Step 4 verify needs a person

Who: Oleg

Question: Verify still fails for 'Filter bundles by reading or sharing state' (write_tests: test writer touched application code (reverted): ['package-lock.json']) and the stronger model could not decide. Answer with {"decision": "retry", "guidance": "<what the writer should do>", "by": "Oleg"} for one more guided round, or any other decision (for example "change_is_wrong") with a "note" to fail the step.

Context:

```json
{
  "kind": "escalation",
  "failure": {
    "check": "write_tests",
    "reason": "test writer touched application code (reverted): ['package-lock.json']",
    "repairable": false,
    "report": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind/verify/rounds/2/write_tests.json"
  },
  "why": "the stronger model gave no usable answer: ",
  "escalation": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind/verify/escalation-1.json",
  "rounds": [
    {
      "round": 1,
      "kind": "write",
      "failure": "revert check: missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmark_list_page_bundle_applies_unread_and_shared_conditions; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_combines_states_with_search_and_tags; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_shared_yes_no_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_filter_unread_yes_no_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_bookmarks_api_bundle_without_states_matches_all_states; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_create_and_get_bundle_returns_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_create_bundle_without_states_defaults_to_off; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_patch_bundle_changes_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateApiTestCase::test_put_bundle_sets_filter_unread_and_filter_shared; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateFormTestCase::test_edit_bundle_form_stores_reading_and_sharing_state; missing-name: bookmarks/tests/test_bundle_filters_blind_api.py::BundleFilterStateFormTestCase::test_new_bundle_form_shows_and_stores_reading_and_sharing_state; missing-name: bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py::BundleFilterStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state; missing-name: bookmarks/tests_e2e/e2e_test_bundle_filters_blind.py::BundleFilterStateE2ETestCase::test_edit_bundle_reading_and_sharing_state"
    },
    {
      "round": 2,
      "kind": "repair",
      "failure": "test writer touched application code (reverted): ['package-lock.json']"
    }
  ],
  "ledger": {
    "caps": {
      "writer_rounds": 3,
      "advice": 2,
      "usd": 8.0
    },
    "spent_usd": 8.3463,
    "writer_rounds_used": 1,
    "advice_used": 1,
    "calls": 3
  }
}
```

Answer by writing /Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind/answer.json, for example {"approved": true, "by": "Oleg", "note": ""}
