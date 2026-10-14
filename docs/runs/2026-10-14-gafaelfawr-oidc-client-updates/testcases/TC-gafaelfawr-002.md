# TC-gafaelfawr-002: An update sets the last-modified time to the moment of the update and leaves the creation time alone

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.last-modified-is-update-time
- role: administrator
- priority: high
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_patch_last_modified_is_time_of_update

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Administrator admin-b has a separate token with the admin:oidc scope
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Note the current UTC time truncated to the whole second, then admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/ and description "Test client", then note the current UTC time again | Response 201; last modified equals created; created lies between the two noted times |
| 2 | Test setup sets the client's creation and last-modified times back to 2020-01-01 12:00:00 UTC in storage, then admin-a reads the client at its Location | Response 200; created and last modified both read 2020-01-01T12:00:00Z |
| 3 | Note the current UTC time truncated to the whole second, then admin-b updates the client with PATCH at its Location, using their own bearer token, return URI https://foo.example.com/other-service and description "Updated description", then note the current UTC time again | Response 200; created is still 2020-01-01 12:00:00 UTC; last modified lies between the two noted times and is later than 2020-01-01 12:00:00 UTC |
| 4 | admin-b reads the client at its Location | Response 200; created is 2020-01-01 12:00:00 UTC; last modified is the same time as in the step 3 response |
| 5 | admin-b lists all clients with GET /auth/api/v1/oidc-clients and finds the client by its client ID | Response 200; the client appears exactly once with created 2020-01-01 12:00:00 UTC and the step 3 last modified time |
| 6 | Check the Slack alert channel | No error alerts were posted |
