"""Tests for the audit fields of updated OpenID Connect clients."""

import re
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from safir.testing.slack import MockSlackWebhook

from gafaelfawr.factory import Factory

from ..support.cookies import set_session_cookie
from ..support.tokens import create_session_token

WHOLE_SECOND_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|\+00:00)$"
)
"""UTC timestamp in whole seconds, without a fractional part."""


def assert_whole_seconds(client_json: dict[str, Any], field: str) -> None:
    """Check that a timestamp field is in UTC with no fractional seconds."""
    assert field in client_json
    assert WHOLE_SECOND_TIMESTAMP.match(client_json[field]), (
        f"{field} is not in whole seconds: {client_json[field]}"
    )


def find_client(
    clients: list[dict[str, Any]], client_id: str
) -> dict[str, Any]:
    """Find a client by ID in the client list."""
    matches = [c for c in clients if c.get("client_id") == client_id]
    assert len(matches) == 1, f"{client_id} not found in {clients}"
    return matches[0]


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_other_admin_records_modifier(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}
    headers_b = {"Authorization": f"Bearer {admin_b.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    created_json = r.json()
    assert created_json["last_modified_by"] == "admin-a"
    assert "created" in created_json
    created = created_json["created"]
    client_id = created_json["client_id"]
    client_url = r.headers["Location"]

    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
            "notes": "Updated by a second administrator",
        },
        headers=headers_b,
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-b"
    assert patch_json["return_uri"] == "https://foo.example.com/other-service"
    assert patch_json["description"] == "Updated description"
    assert patch_json["notes"] == "Updated by a second administrator"
    assert patch_json["created"] == created
    assert "last_modified" in patch_json
    assert "client_secret" not in patch_json

    # Both retrieval routes, whichever administrator calls them, show the
    # updated client with the same audit fields as the PATCH response.
    r = await client.get(client_url, headers=headers_a)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients", headers=headers_a)
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert "last_modified_by" in seen
        assert seen["last_modified_by"] == "admin-b"
        assert seen["return_uri"] == "https://foo.example.com/other-service"
        assert seen["description"] == "Updated description"
        assert seen["notes"] == "Updated by a second administrator"
        assert seen["created"] == created
        assert "last_modified" in seen
        assert seen["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_last_modified_not_before_send_time(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}
    headers_b = {"Authorization": f"Bearer {admin_b.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Test client",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    post_json = r.json()
    assert_whole_seconds(post_json, "created")
    assert_whole_seconds(post_json, "last_modified")
    assert post_json["last_modified"] == post_json["created"]
    created = datetime.fromisoformat(post_json["created"])
    client_id = post_json["client_id"]
    client_url = r.headers["Location"]

    before = datetime.now(tz=UTC).replace(microsecond=0)
    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
        },
        headers=headers_b,
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert_whole_seconds(patch_json, "created")
    assert_whole_seconds(patch_json, "last_modified")
    assert datetime.fromisoformat(patch_json["created"]) == created
    last_modified = datetime.fromisoformat(patch_json["last_modified"])
    assert last_modified >= before
    assert last_modified >= created

    r = await client.get(client_url, headers=headers_b)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients", headers=headers_b)
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert_whole_seconds(seen, "created")
        assert_whole_seconds(seen, "last_modified")
        assert datetime.fromisoformat(seen["created"]) == created
        assert datetime.fromisoformat(seen["last_modified"]) == last_modified

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_creator_keeps_creator_as_modifier(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    creator = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    headers = {"Authorization": f"Bearer {creator.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Test client",
        },
        headers=headers,
    )
    assert r.status_code == 201
    post_json = r.json()
    assert post_json["last_modified_by"] == "admin-a"
    created = post_json["created"]
    client_url = r.headers["Location"]

    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
            "notes": "Updated by the creator",
        },
        headers=headers,
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-a"
    assert patch_json["created"] == created
    assert "last_modified" in patch_json
    last_modified = datetime.fromisoformat(patch_json["last_modified"])
    assert last_modified >= datetime.fromisoformat(created)

    r = await client.get(client_url, headers=headers)
    assert r.status_code == 200
    get_json = r.json()
    assert "last_modified_by" in get_json
    assert get_json["last_modified_by"] == "admin-a"
    assert get_json["notes"] == "Updated by the creator"
    assert get_json["created"] == created
    assert get_json["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_other_admin_via_session_cookie(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
            "notes": "Notes to be cleared",
        },
        headers={"Authorization": f"Bearer {admin_a.token}"},
    )
    assert r.status_code == 201
    created_json = r.json()
    assert created_json["last_modified_by"] == "admin-a"
    created = created_json["created"]
    client_id = created_json["client_id"]
    client_url = r.headers["Location"]

    # From here on, only the session cookie of the second administrator
    # authenticates the requests. A body without notes clears them.
    csrf = await set_session_cookie(client, admin_b.token)
    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated with a cookie",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-b"
    assert patch_json["description"] == "Updated with a cookie"
    assert "notes" in patch_json
    assert patch_json["notes"] is None
    assert patch_json["created"] == created

    r = await client.get(client_url)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients")
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert "last_modified_by" in seen
        assert seen["last_modified_by"] == "admin-b"
        assert seen["return_uri"] == "https://foo.example.com/other-service"
        assert seen["description"] == "Updated with a cookie"
        assert "notes" not in seen
        assert seen["created"] == created
        assert seen["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_refused_patch_leaves_client_unchanged(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    user = await create_session_token(
        factory, username="some-user", scopes={"user:token"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    client_url = r.headers["Location"]
    r = await client.get(client_url, headers=headers_a)
    assert r.status_code == 200
    original = r.json()
    assert original["last_modified_by"] == "admin-a"

    update = {
        "return_uri": "https://foo.example.com/other-service",
        "description": "Updated description",
        "notes": "Should never be stored",
    }
    r = await client.patch(client_url, json=update)
    assert r.status_code == 401
    r = await client.patch(
        client_url,
        json=update,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert r.status_code == 403
    r = await client.patch(
        client_url,
        json={"return_uri": "https://foo.example.com/other-service"},
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 422
    r = await client.patch(
        client_url,
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 422
    r = await client.patch(
        "/auth/api/v1/oidc-clients/unknown-client.clients.example.com",
        json=update,
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 404

    r = await client.get(client_url, headers=headers_a)
    assert r.status_code == 200
    assert r.json() == original

    assert mock_slack.messages == []
