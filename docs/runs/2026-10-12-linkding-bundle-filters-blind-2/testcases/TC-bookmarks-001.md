# TC-bookmarks-001: A bundle created through the API stores its reading and sharing state, and both default to off

- area: bookmarks
- tiles: bookmarks.bundles.filter-state-fields-stored-and-default-off
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_create_and_get_bundle_with_filter_unread_and_filter_shared

## Preconditions

- The user is authenticated against the REST API with their API token

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /api/bundles/ with name "Unread unshared", search "python", filter_unread "yes", filter_shared "no" | 201 Created; the response carries the new bundle's id |
| 2 | POST /api/bundles/ with name "Read shared", search "python", filter_unread "no", filter_shared "yes" | 201 Created; the response carries the new bundle's id |
| 3 | POST /api/bundles/ with only the name "Defaults" | 201 Created; the response carries the new bundle's id |
| 4 | GET /api/bundles/ID/ where ID is the id of "Unread unshared" | 200 OK; filter_unread is "yes" and filter_shared is "no" |
| 5 | GET /api/bundles/ID/ where ID is the id of "Read shared" | 200 OK; filter_unread is "no" and filter_shared is "yes" |
| 6 | GET /api/bundles/ID/ where ID is the id of "Defaults" | 200 OK; filter_unread is "off" and filter_shared is "off" |
| 7 | GET /api/bundles/ | 200 OK; the results include "Unread unshared" with filter_unread "yes" and filter_shared "no", and "Defaults" with filter_unread "off" and filter_shared "off" |
