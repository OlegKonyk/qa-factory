# TC-bookmarks-006: Archived bookmark list can be sorted by Modified ↓ from the sort dropdown

- area: bookmarks
- tiles: bookmarks.sort.archived-list-modified-descending
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests_e2e/e2e_test_sort_by_modified.py::SortByModifiedE2ETestCase::test_sort_archived_bookmarks_by_modified

## Preconditions

- The user is logged in to the web interface
- The user has three archived bookmarks (dates in UTC): "Alpha" added 2020-01-01 and modified 2022-01-01, "Bravo" added 2021-01-01 and modified 2020-01-01, "Charlie" added 2022-01-01 and modified 2021-01-01

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Open the archived bookmarks page | The list shows Charlie, Bravo, Alpha in that order (newest added first) |
| 2 | Click the "Search preferences" button | The preferences menu opens and its sort dropdown includes the options "Modified ↑" and "Modified ↓" |
| 3 | Select "Modified ↓" in the sort dropdown and click "Apply" | The page address contains sort=modified_desc and the list shows Alpha, Charlie, Bravo in that order |
