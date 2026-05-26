"""Tests for the Agent CRUD API endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_agent(client: AsyncClient, sample_agent_data: dict):
    """POST /api/agents with valid data returns 201 and the created agent."""
    resp = await client.post("/api/agents/", json=sample_agent_data)
    assert resp.status_code == 201

    body = resp.json()
    assert body["name"] == sample_agent_data["name"]
    assert body["role"] == sample_agent_data["role"]
    assert body["system_prompt"] == sample_agent_data["system_prompt"]
    assert body["model"] == sample_agent_data["model"]
    assert body["tools"] == sample_agent_data["tools"]
    assert body["temperature"] == sample_agent_data["temperature"]
    assert body["max_tokens"] == sample_agent_data["max_tokens"]
    assert body["memory_enabled"] == sample_agent_data["memory_enabled"]
    assert body["memory_window"] == sample_agent_data["memory_window"]
    # Should have an id and timestamps
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body
    # Verify the id is a valid UUID
    uuid.UUID(body["id"])


async def test_create_agent_minimal(client: AsyncClient):
    """POST /api/agents with only required fields succeeds with defaults."""
    payload = {
        "name": "Minimal Agent",
        "role": "helper",
        "system_prompt": "You help.",
    }
    resp = await client.post("/api/agents/", json=payload)
    assert resp.status_code == 201

    body = resp.json()
    assert body["name"] == "Minimal Agent"
    assert body["role"] == "helper"
    assert body["system_prompt"] == "You help."
    # Defaults should be applied
    assert body["model"] == "gpt-4o-mini"
    assert body["tools"] == []
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 4096
    assert body["memory_enabled"] is True
    assert body["memory_window"] == 20


async def test_list_agents(client: AsyncClient, sample_agent_data: dict):
    """GET /api/agents returns all created agents."""
    # Create two agents
    data1 = {**sample_agent_data, "name": "Agent One"}
    data2 = {**sample_agent_data, "name": "Agent Two"}
    await client.post("/api/agents/", json=data1)
    await client.post("/api/agents/", json=data2)

    resp = await client.get("/api/agents/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 2

    names = {a["name"] for a in body}
    assert "Agent One" in names
    assert "Agent Two" in names


async def test_get_agent(client: AsyncClient, sample_agent_data: dict):
    """GET /api/agents/{id} returns the correct agent."""
    create_resp = await client.post("/api/agents/", json=sample_agent_data)
    agent_id = create_resp.json()["id"]

    resp = await client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == agent_id
    assert body["name"] == sample_agent_data["name"]
    assert body["role"] == sample_agent_data["role"]


async def test_get_agent_not_found(client: AsyncClient):
    """GET /api/agents/{id} with non-existent id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/agents/{fake_id}")
    assert resp.status_code == 404


async def test_update_agent(client: AsyncClient, sample_agent_data: dict):
    """PUT /api/agents/{id} updates the specified fields."""
    create_resp = await client.post("/api/agents/", json=sample_agent_data)
    agent_id = create_resp.json()["id"]

    update_payload = {
        "name": "Updated Agent Name",
        "temperature": 0.9,
        "max_tokens": 8192,
    }
    resp = await client.put(f"/api/agents/{agent_id}", json=update_payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["name"] == "Updated Agent Name"
    assert body["temperature"] == 0.9
    assert body["max_tokens"] == 8192
    # Non-updated fields should remain unchanged
    assert body["role"] == sample_agent_data["role"]
    assert body["system_prompt"] == sample_agent_data["system_prompt"]


async def test_delete_agent(client: AsyncClient, sample_agent_data: dict):
    """DELETE /api/agents/{id} removes the agent; re-fetch returns 404."""
    create_resp = await client.post("/api/agents/", json=sample_agent_data)
    agent_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/agents/{agent_id}")
    assert delete_resp.status_code == 204

    # Re-fetch should yield 404
    get_resp = await client.get(f"/api/agents/{agent_id}")
    assert get_resp.status_code == 404


async def test_delete_agent_not_found(client: AsyncClient):
    """DELETE /api/agents/{id} with non-existent id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/agents/{fake_id}")
    assert resp.status_code == 404


async def test_create_agent_missing_fields(client: AsyncClient):
    """POST /api/agents without the required 'name' field returns 422."""
    payload = {
        "role": "assistant",
        "system_prompt": "Hello",
    }
    resp = await client.post("/api/agents/", json=payload)
    assert resp.status_code == 422


async def test_create_agent_empty_name(client: AsyncClient):
    """POST /api/agents with an empty name returns 422 (min_length=1)."""
    payload = {
        "name": "",
        "role": "assistant",
        "system_prompt": "Hello",
    }
    resp = await client.post("/api/agents/", json=payload)
    assert resp.status_code == 422
