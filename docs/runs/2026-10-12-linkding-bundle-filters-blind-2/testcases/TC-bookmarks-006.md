# TC-bookmarks-006: The new-bundle form offers reading and sharing state, previews the matches and saves the choice

- area: bookmarks
- tiles: bookmarks.bundles.form-new-reading-sharing-state
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests_e2e/e2e_test_bundle_filters_blind_2.py::BundleReadingSharingStateE2ETestCase::test_create_bundle_with_reading_and_sharing_state

## Preconditions

- The user is logged in to the web app
- Sharing is enabled in the user's settings
- The user has the bookmarks "Inbox Public 1" and "Inbox Public 2" (unread, shared)
- The user has the bookmark "Inbox Private 1" (unread, unshared)
- The user has the bookmark "Done Public 1" (read, shared)
- The user has the bookmarks "Done Private 1", "Done Private 2" and "Done Private 3" (read, unshared)

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Open /bundles/new | A "Reading State" dropdown with the options All, Unread, Read and a "Sharing State" dropdown with the options All, Shared, Unshared are visible; both show "All" |
| 2 | Look at the preview below the form | "Found 7 bookmarks matching this bundle." is shown and exactly the 7 bookmarks are listed |
| 3 | Enter "Unread and shared" in the Name field | The name is filled in |
| 4 | Choose "Unread" in the Reading State dropdown | "Found 3 bookmarks matching this bundle." is shown; exactly Inbox Public 1, Inbox Public 2 and Inbox Private 1 are listed |
| 5 | Choose "Shared" in the Sharing State dropdown | "Found 2 bookmarks matching this bundle." is shown; exactly Inbox Public 1 and Inbox Public 2 are listed |
| 6 | Click Save | "Bundle saved successfully." is shown |
| 7 | Open the bookmark list page /bookmarks?bundle=ID where ID is the id of the new bundle "Unread and shared" | Exactly Inbox Public 1 and Inbox Public 2 are listed |
| 8 | Open the edit form /bundles/ID/edit for the same bundle | Both dropdowns are visible with the same options; Reading State shows "Unread" and Sharing State shows "Shared"; "Found 2 bookmarks matching this bundle." is shown |
