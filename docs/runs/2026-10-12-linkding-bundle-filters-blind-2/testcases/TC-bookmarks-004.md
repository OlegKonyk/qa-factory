# TC-bookmarks-004: A bundle's sharing state limits its bookmarks to shared, to unshared, or to both

- area: bookmarks
- tiles: bookmarks.bundles.filter-shared-yes-no-off
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_shared_yes_no_off

## Preconditions

- The user is authenticated against the REST API with their API token
- A unique search word is chosen for this run
- The user has 3 shared bookmarks whose titles contain the search word
- The user has 2 unshared bookmarks whose titles contain the search word
- The user has 2 shared and 2 unshared bookmarks whose titles do not contain the search word

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /api/bundles/ with name "Shared", search set to the search word, filter_shared "yes" | 201 Created; the response carries the new bundle's id |
| 2 | POST /api/bundles/ with name "Unshared", search set to the search word, filter_shared "no" | 201 Created; the response carries the new bundle's id |
| 3 | POST /api/bundles/ with name "All", search set to the search word, filter_shared "off" | 201 Created; the response carries the new bundle's id |
| 4 | GET /api/bookmarks/?bundle=ID where ID is the id of "Shared" | 200 OK; the results are exactly the 3 shared bookmarks containing the search word |
| 5 | GET /api/bookmarks/?bundle=ID where ID is the id of "Unshared" | 200 OK; the results are exactly the 2 unshared bookmarks containing the search word |
| 6 | GET /api/bookmarks/?bundle=ID where ID is the id of "All" | 200 OK; the results are exactly the 5 bookmarks containing the search word, shared and unshared; none of the 4 other bookmarks appear |
