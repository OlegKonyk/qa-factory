# Step 4 verify needs a person

Who: Oleg

Question: Approve the generated tests and their test cases for 'Filter bundles by reading or sharing state' so they join the application's suite?

Context:

```json
{
  "tests": [
    "bookmarks/tests/test_bundle_filters_blind_2_api.py",
    "bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py"
  ],
  "test_files_copy": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind-2/verify/tests",
  "test_cases": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind-2/verify/testcases",
  "revert_check": {
    "bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_combines_unread_shared_search_and_tags": "proves-behaviour",
    "bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_shared_yes_no_off": "proves-behaviour",
    "bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_unread_yes_no_off": "proves-behaviour",
    "bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_create_and_get_bundle_with_filter_unread_and_filter_shared": "proves-behaviour",
    "bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_patch_bundle_changes_filter_fields_and_keeps_others": "proves-behaviour",
    "bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py::BundleReadingSharingStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state": "proves-behaviour",
    "bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py::BundleReadingSharingStateE2ETestCase::test_edit_bundle_reading_and_sharing_state": "proves-behaviour"
  },
  "mutation": {
    "generated": {
      "checked": 82,
      "killed": 51,
      "survived": 31,
      "score": 0.6219512195121951,
      "on_changed_lines": {
        "checked": 16,
        "killed": 16,
        "survived": 0,
        "score": 1.0
      }
    },
    "generated_and_developers": {
      "checked": 82,
      "killed": 77,
      "survived": 5,
      "score": 0.9390243902439024,
      "on_changed_lines": {
        "checked": 16,
        "killed": 16,
        "survived": 0,
        "score": 1.0
      }
    },
    "developers": {
      "checked": 82,
      "killed": 77,
      "survived": 5,
      "score": 0.9390243902439024,
      "on_changed_lines": {
        "checked": 16,
        "killed": 16,
        "survived": 0,
        "score": 1.0
      }
    }
  },
  "suite": [
    "============================ 1280 passed in 24.08s =============================",
    "=================== 83 passed, 1 skipped in 70.57s (0:01:10) ==================="
  ],
  "cost_usd": 4.9392,
  "time_s": {
    "write_tests": 448.3,
    "lint": 0.1,
    "revert": 20.4,
    "mutation.generated": 17.1,
    "mutation.generated_and_developers": 81.7,
    "mutation.developers": 85.3,
    "mutation": 184.1,
    "suite": 97.3,
    "test_cases": 217.7
  }
}
```

Answer by writing /Users/oleg/dev/qa-factory/.artifacts/runs/linkding-bundle-filters-blind-2/answer.json, for example {"approved": true, "by": "Oleg", "note": ""}

Under Restate, answer over HTTP instead of writing the file:

    curl -X POST http://localhost:8080/factory/linkding-bundle-filters-blind-2/answer -H 'content-type: application/json' -d '{"approved": true, "by": "Oleg", "note": ""}'
