# Step 4 verify needs a person

Who: Oleg

Question: Approve the generated tests and their test cases for 'Add sort by modification date option' so they join the application's suite?

Context:

```json
{
  "tests": [
    "bookmarks/tests/test_sort_by_modified_api.py",
    "bookmarks/tests_e2e/e2e_test_sort_by_modified.py"
  ],
  "test_files_copy": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-sort-by-modified/verify/tests",
  "test_cases": "/Users/oleg/dev/qa-factory/.artifacts/runs/linkding-sort-by-modified/verify/testcases",
  "revert_check": {
    "bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_archived_bookmarks_sort_modified_asc_and_desc": "proves-behaviour",
    "bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_bookmarks_sort_modified_asc": "proves-behaviour",
    "bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_bookmarks_sort_modified_desc": "proves-behaviour",
    "bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_bookmarks_unknown_sort_falls_back_to_default_order": "passes-without-change",
    "bookmarks/tests_e2e/e2e_test_sort_by_modified.py::SortByModifiedE2ETestCase::test_sort_archived_bookmarks_by_modified": "proves-behaviour",
    "bookmarks/tests_e2e/e2e_test_sort_by_modified.py::SortByModifiedE2ETestCase::test_sort_bookmarks_by_modified_asc_and_desc": "proves-behaviour"
  },
  "mutation": {
    "generated": {
      "checked": 108,
      "killed": 27,
      "survived": 81,
      "score": 0.25,
      "on_changed_lines": {
        "checked": 10,
        "killed": 10,
        "survived": 0,
        "score": 1.0
      }
    },
    "generated_and_developers": {
      "checked": 108,
      "killed": 98,
      "survived": 10,
      "score": 0.9074074074074074,
      "on_changed_lines": {
        "checked": 10,
        "killed": 10,
        "survived": 0,
        "score": 1.0
      }
    }
  },
  "suite": [
    "============================ 1294 passed in 24.18s =============================",
    "=================== 83 passed, 1 skipped in 68.13s (0:01:08) ==================="
  ],
  "cost_usd": 4.9005,
  "time_s": {
    "write_tests": 413.8,
    "lint": 0.1,
    "revert": 17.9,
    "mutation.generated": 21.3,
    "mutation.generated_and_developers": 137.8,
    "mutation": 159.2,
    "suite": 93.3,
    "test_cases": 115.5
  }
}
```

Answer by writing /Users/oleg/dev/qa-factory/.artifacts/runs/linkding-sort-by-modified/answer.json, for example {"approved": true, "by": "Oleg", "note": ""}
