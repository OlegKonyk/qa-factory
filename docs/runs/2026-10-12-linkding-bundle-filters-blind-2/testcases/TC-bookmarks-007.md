# TC-bookmarks-007: The edit-bundle form changes reading and sharing state, previews the matches and saves the choice

- area: bookmarks
- tiles: bookmarks.bundles.form-edit-reading-sharing-state
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py::BundleReadingSharingStateE2ETestCase::test_edit_bundle_reading_and_sharing_state

## Preconditions

- The user is logged in to the web app
- Sharing is enabled in the user's settings
- The user has the bookmarks "Inbox Public 1" and "Inbox Public 2" (unread, shared)
- The user has the bookmark "Inbox Private 1" (unread, unshared)
- The user has the bookmark "Done Public 1" (read, shared)
- The user has the bookmarks "Done Private 1", "Done Private 2" and "Done Private 3" (read, unshared)
- The user has a bundle "Edited bundle" with no search, no tags, and reading and sharing state off

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Open the edit form /bundles/ID/edit where ID is the id of "Edited bundle" | A "Reading State" dropdown with the options All, Unread, Read and a "Sharing State" dropdown with the options All, Shared, Unshared are visible; both show "All"; "Found 7 bookmarks matching this bundle." is shown |
| 2 | Choose "Read" in the Reading State dropdown and "Unshared" in the Sharing State dropdown | "Found 3 bookmarks matching this bundle." is shown; exactly Done Private 1, Done Private 2 and Done Private 3 are listed |
| 3 | Click Save | "Bundle saved successfully." is shown |
| 4 | Open the bookmark list page /bookmarks?bundle=ID for "Edited bundle" | Exactly Done Private 1, Done Private 2 and Done Private 3 are listed |
| 5 | Open the edit form /bundles/ID/edit for "Edited bundle" again | Reading State shows "Read" and Sharing State shows "Unshared"; "Found 3 bookmarks matching this bundle." is shown |
