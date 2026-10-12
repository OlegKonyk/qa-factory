# TC-bookmarks-003: A bundle's reading state limits its bookmarks to unread, to read, or to both

- area: bookmarks
- tiles: bookmarks.bundles.filter-unread-yes-no-off
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_bookmarks_by_bundle_filter_unread_yes_no_off

## Preconditions

- The user is authenticated against the REST API with their API token
- A unique search word is chosen for this run
- The user has 3 unread bookmarks whose titles contain the search word
- The user has 2 read bookmarks whose titles contain the search word
- The user has 2 unread and 2 read bookmarks whose titles do not contain the search word

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /api/bundles/ with name "Unread", search set to the search word, filter_unread "yes" | 201 Created; the response carries the new bundle's id |
| 2 | POST /api/bundles/ with name "Read", search set to the search word, filter_unread "no" | 201 Created; the response carries the new bundle's id |
| 3 | POST /api/bundles/ with name "All", search set to the search word, filter_unread "off" | 201 Created; the response carries the new bundle's id |
| 4 | GET /api/bookmarks/?bundle=ID where ID is the id of "Unread" | 200 OK; the results are exactly the 3 unread bookmarks containing the search word |
| 5 | GET /api/bookmarks/?bundle=ID where ID is the id of "Read" | 200 OK; the results are exactly the 2 read bookmarks containing the search word |
| 6 | GET /api/bookmarks/?bundle=ID where ID is the id of "All" | 200 OK; the results are exactly the 5 bookmarks containing the search word, read and unread; none of the 4 other bookmarks appear |
