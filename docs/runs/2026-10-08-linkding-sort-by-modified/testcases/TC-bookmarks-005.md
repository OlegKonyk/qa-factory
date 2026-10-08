# TC-bookmarks-005: Bookmark list offers Modified ↑ and Modified ↓ sorting and reorders the list for each

- area: bookmarks
- tiles: bookmarks.sort.list-modified-options
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests_e2e/e2e_test_sort_by_modified.py::SortByModifiedE2ETestCase::test_sort_bookmarks_by_modified_asc_and_desc

## Preconditions

- The user is logged in to the web interface
- The user has three unarchived bookmarks (dates in UTC): "Alpha" added 2020-01-01 and modified 2022-01-01, "Bravo" added 2021-01-01 and modified 2020-01-01, "Charlie" added 2022-01-01 and modified 2021-01-01

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Open the bookmarks page | The list shows Charlie, Bravo, Alpha in that order (newest added first) |
| 2 | Click the "Search preferences" button | The preferences menu opens and its sort dropdown includes the options "Modified ↑" and "Modified ↓" |
| 3 | Select "Modified ↑" in the sort dropdown and click "Apply" | The page address contains sort=modified_asc and the list shows Bravo, Charlie, Alpha in that order |
| 4 | Click the "Search preferences" button again | The preferences menu opens and its sort dropdown still includes "Modified ↑" and "Modified ↓" |
| 5 | Select "Modified ↓" in the sort dropdown and click "Apply" | The page address contains sort=modified_desc and the list shows Alpha, Charlie, Bravo in that order |
