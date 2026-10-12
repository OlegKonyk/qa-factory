# TC-bookmarks-002: PATCH on a bundle changes its reading and sharing state and leaves its other conditions alone

- area: bookmarks
- tiles: bookmarks.bundles.filter-state-patch
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_bundle_filters_blind_2_api.py::BundleReadingSharingFiltersApiTestCase::test_patch_bundle_changes_filter_fields_and_keeps_others

## Preconditions

- The user is authenticated against the REST API with their API token

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /api/bundles/ with name "Patched bundle", search "python", any_tags "programming", all_tags "required", excluded_tags "excluded" and no reading or sharing state | 201 Created; the response carries the new bundle's id (ID below) |
| 2 | PATCH /api/bundles/ID/ with only filter_unread "no" | 200 OK |
| 3 | GET /api/bundles/ID/ | 200 OK; filter_unread is "no"; filter_shared is still "off" |
| 4 | PATCH /api/bundles/ID/ with only filter_shared "yes" | 200 OK |
| 5 | GET /api/bundles/ID/ | 200 OK; filter_unread is still "no"; filter_shared is "yes" |
| 6 | PATCH /api/bundles/ID/ with filter_unread "yes" and filter_shared "no" | 200 OK |
| 7 | GET /api/bundles/ID/ | 200 OK; filter_unread is "yes" and filter_shared is "no"; name is still "Patched bundle", search "python", any_tags "programming", all_tags "required", excluded_tags "excluded" |
| 8 | PATCH /api/bundles/ID/ with filter_unread "off" and filter_shared "off" | 200 OK |
| 9 | GET /api/bundles/ID/ | 200 OK; filter_unread is "off" and filter_shared is "off" |
