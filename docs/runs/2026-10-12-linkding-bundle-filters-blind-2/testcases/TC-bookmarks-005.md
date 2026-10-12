# TC-bookmarks-005: Reading state, sharing state, search and tag conditions of a bundle all apply together

- area: bookmarks
- tiles: bookmarks.bundles.filters-combine-with-search-and-tags
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_combines_unread_shared_search_and_tags

## Preconditions

- The user is authenticated against the REST API with their API token and is logged in to the web app
- A unique search word is chosen for this run
- The user has the tags "required" and "excluded"
- Four bookmarks contain the search word and are tagged "required": one unread and shared, one unread and unshared, one read and shared, one read and unshared
- Three unread and shared bookmarks each miss one other condition: one lacks the search word (tagged "required"), one contains the search word but has no tag, one contains the search word and is tagged both "required" and "excluded"
- Two read and unshared bookmarks each miss one other condition: one lacks the search word (tagged "required"), one contains the search word but has no tag

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /api/bundles/ with name "Unread and shared", search set to the search word, all_tags "required", excluded_tags "excluded", filter_unread "yes", filter_shared "yes" | 201 Created; the response carries the new bundle's id |
| 2 | POST /api/bundles/ with name "Read and unshared", the same search and tags, filter_unread "no", filter_shared "no" | 201 Created; the response carries the new bundle's id |
| 3 | POST /api/bundles/ with name "Unread, any sharing state", the same search and tags, filter_unread "yes", filter_shared "off" | 201 Created; the response carries the new bundle's id |
| 4 | GET /api/bookmarks/?bundle=ID where ID is the id of "Unread and shared" | 200 OK; the only result is the unread, shared bookmark that has the search word and the "required" tag |
| 5 | GET /api/bookmarks/?bundle=ID where ID is the id of "Read and unshared" | 200 OK; the only result is the read, unshared bookmark that has the search word and the "required" tag |
| 6 | GET /api/bookmarks/?bundle=ID where ID is the id of "Unread, any sharing state" | 200 OK; the results are exactly the two unread bookmarks (shared and unshared) that have the search word and the "required" tag |
| 7 | Open the bookmark list page /bookmarks?bundle=ID where ID is the id of "Unread and shared" | The page loads; the unread, shared bookmark with the search word and "required" tag is listed; none of the other 8 bookmarks are listed |
| 8 | Open the bookmark list page /bookmarks?bundle=ID where ID is the id of "Read and unshared" | The page loads; the read, unshared bookmark with the search word and "required" tag is listed; none of the other 8 bookmarks are listed |
