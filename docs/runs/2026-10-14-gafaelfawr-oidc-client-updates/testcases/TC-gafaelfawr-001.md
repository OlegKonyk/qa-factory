# TC-gafaelfawr-001: An update by a second administrator records that administrator as the last modifier

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.records-modifier
- role: administrator
- priority: high
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_patch_by_other_admin_records_modifier

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Administrator admin-b has a separate token with the admin:oidc scope
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/ and description "Original description" | Response 201 with a Location header for the new client; last modified by is admin-a |
| 2 | Test setup sets the client's creation and last-modified times back to 2020-01-01 12:00:00 UTC in storage, then admin-a reads the client at its Location | Response 200; created and last modified both read 2020-01-01T12:00:00Z |
| 3 | admin-b updates the client with PATCH at its Location, using their own bearer token, return URI https://foo.example.com/other-service, description "Updated description" and notes "Updated by a second administrator" | Response 200; last modified by is admin-b; return URI, description and notes show the new values; created is still 2020-01-01T12:00:00Z; last modified is present and no longer 2020-01-01T12:00:00Z; no client secret appears in the response |
| 4 | admin-a reads the client at its Location | Response 200; last modified by is admin-b; return URI, description and notes show the values from step 3; created is 2020-01-01T12:00:00Z; last modified is the same value as in the step 3 response |
| 5 | admin-a lists all clients with GET /auth/api/v1/oidc-clients and finds the client by its client ID | Response 200; the client appears exactly once and shows the same values as in step 4, including last modified by admin-b and the step 3 last modified time |
| 6 | Check the Slack alert channel | No error alerts were posted |
