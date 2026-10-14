# TC-gafaelfawr-004: An update by the creator keeps the creator as last modifier and moves the last-modified time

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.creator-stays-modifier
- role: administrator
- priority: medium
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_patch_by_creator_keeps_creator_as_modifier

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/ and description "Test client" | Response 201 with a Location header for the new client; last modified by is admin-a |
| 2 | Test setup sets the client's creation and last-modified times back to 2020-01-01 12:00:00 UTC in storage, then admin-a reads the client at its Location | Response 200; created and last modified both read 2020-01-01T12:00:00Z |
| 3 | Note the current UTC time truncated to the whole second, then admin-a updates the client with PATCH at its Location, using the same bearer token, return URI https://foo.example.com/other-service, description "Updated description" and notes "Updated by the creator", then note the current UTC time again | Response 200; last modified by is still admin-a; created is still 2020-01-01T12:00:00Z; last modified is present and lies between the two noted times |
| 4 | admin-a reads the client at its Location | Response 200; last modified by is admin-a; notes read "Updated by the creator"; created is 2020-01-01T12:00:00Z; last modified is the same value as in the step 3 response |
| 5 | Check the Slack alert channel | No error alerts were posted |
