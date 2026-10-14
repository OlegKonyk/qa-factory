# TC-gafaelfawr-003: Creation and last-modified times are shown in whole UTC seconds on create, update, read and list

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.timestamps-whole-seconds
- role: administrator
- priority: medium
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_timestamps_in_whole_seconds

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Administrator admin-b has a separate token with the admin:oidc scope
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/ and description "Test client" | Response 201; created and last modified are both present and written as a UTC time in whole seconds with no fractional part, in the form 2026-10-14T15:44:22Z |
| 2 | admin-b updates the client with PATCH at its Location, using their own bearer token, return URI https://foo.example.com/other-service and description "Updated description" | Response 200; created and last modified are both present and written in whole UTC seconds with no fractional part |
| 3 | admin-b reads the client at its Location | Response 200; created and last modified are both written in whole UTC seconds with no fractional part |
| 4 | admin-b lists all clients with GET /auth/api/v1/oidc-clients and finds the client by its client ID | Response 200; the client appears exactly once; its created and last modified are both written in whole UTC seconds with no fractional part |
| 5 | Check the Slack alert channel | No error alerts were posted |
