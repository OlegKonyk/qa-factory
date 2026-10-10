# TC-bookmarks-004: The sort dropdown offers Modified ↑ and Modified ↓ and choosing one reorders the bookmark list

- area: bookmarks
- tiles: bookmarks.sort.modified-dropdown-reorders-list
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests_e2e/e2e_test_sort_by_modified_blind.py::SortByModifiedE2ETestCase::test_sort_dropdown_modified_options_reorder_list

## Preconditions

- The user is logged in to the web interface
- The user owns bookmark "Oldest added, middle modified" (added 30 days ago, modified 5 days ago)
- The user owns bookmark "Middle added, oldest modified" (added 20 days ago, modified 10 days ago)
- The user owns bookmark "Newest added, newest modified" (added 10 days ago, modified 1 day ago)

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Open the bookmarks page | Exactly three bookmarks, in the default order (newest added first): "Newest added, newest modified", "Middle added, oldest modified", "Oldest added, middle modified" |
| 2 | Click the "Search preferences" button | The preferences panel opens with a visible Sort selector that contains exactly one "Modified ↑" option and exactly one "Modified ↓" option |
| 3 | Choose "Modified ↑" in the Sort selector and click "Apply" | Exactly three bookmarks, oldest modified first: "Middle added, oldest modified", "Oldest added, middle modified", "Newest added, newest modified" |
| 4 | Click "Search preferences" again, choose "Modified ↓" in the Sort selector and click "Apply" | Exactly three bookmarks, newest modified first: "Newest added, newest modified", "Oldest added, middle modified", "Middle added, oldest modified" |
