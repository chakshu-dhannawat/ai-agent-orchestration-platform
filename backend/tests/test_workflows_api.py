"""Tests for the Workflow CRUD API endpoints."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_workflow(client: AsyncClient, sample_workflow_data: dict):
    """POST /api/workflows with a valid graph_definition returns 201."""
    resp = await client.post("/api/workflows/", json=sample_workflow_data)
    assert resp.status_code == 201

    body = resp.json()
    assert body["name"] == sample_workflow_data["name"]
    assert body["description"] == sample_workflow_data["description"]
    assert body["is_template"] == sample_workflow_data["is_template"]
    assert body["graph_definition"] == sample_workflow_data["graph_definition"]
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body
    uuid.UUID(body["id"])


async def test_list_workflows(client: AsyncClient, sample_workflow_data: dict):
    """GET /api/workflows returns all non-template workflows."""
    data1 = {**sample_workflow_data, "name": "Workflow A"}
    data2 = {**sample_workflow_data, "name": "Workflow B"}
    await client.post("/api/workflows/", json=data1)
    await client.post("/api/workflows/", json=data2)

    resp = await client.get("/api/workflows/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 2

    names = {w["name"] for w in body}
    assert "Workflow A" in names
    assert "Workflow B" in names


async def test_get_workflow(client: AsyncClient, sample_workflow_data: dict):
    """GET /api/workflows/{id} returns the correct workflow."""
    create_resp = await client.post("/api/workflows/", json=sample_workflow_data)
    workflow_id = create_resp.json()["id"]

    resp = await client.get(f"/api/workflows/{workflow_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == workflow_id
    assert body["name"] == sample_workflow_data["name"]


async def test_get_workflow_not_found(client: AsyncClient):
    """GET /api/workflows/{id} with non-existent id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/workflows/{fake_id}")
    assert resp.status_code == 404


async def test_update_workflow(client: AsyncClient, sample_workflow_data: dict):
    """PUT /api/workflows/{id} updates the specified fields."""
    create_resp = await client.post("/api/workflows/", json=sample_workflow_data)
    workflow_id = create_resp.json()["id"]

    update_payload = {
        "name": "Updated Workflow",
        "description": "Updated description",
    }
    resp = await client.put(f"/api/workflows/{workflow_id}", json=update_payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["name"] == "Updated Workflow"
    assert body["description"] == "Updated description"
    # Graph definition should remain unchanged
    assert body["graph_definition"] == sample_workflow_data["graph_definition"]


async def test_delete_workflow(client: AsyncClient, sample_workflow_data: dict):
    """DELETE /api/workflows/{id} removes the workflow; re-fetch returns 404."""
    create_resp = await client.post("/api/workflows/", json=sample_workflow_data)
    workflow_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/workflows/{workflow_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/workflows/{workflow_id}")
    assert get_resp.status_code == 404


async def test_delete_workflow_not_found(client: AsyncClient):
    """DELETE /api/workflows/{id} with non-existent id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/workflows/{fake_id}")
    assert resp.status_code == 404


async def test_validate_workflow_valid(client: AsyncClient, sample_workflow_data: dict):
    """POST /api/workflows/{id}/validate with a valid graph returns valid=True."""
    create_resp = await client.post("/api/workflows/", json=sample_workflow_data)
    workflow_id = create_resp.json()["id"]

    resp = await client.post(f"/api/workflows/{workflow_id}/validate")
    assert resp.status_code == 200

    body = resp.json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["node_count"] == 2
    assert body["edge_count"] == 1


async def test_validate_workflow_empty_graph(client: AsyncClient):
    """POST /api/workflows/{id}/validate with an empty graph returns valid=False."""
    data = {
        "name": "Empty Workflow",
        "description": "No graph",
        "graph_definition": {},
    }
    create_resp = await client.post("/api/workflows/", json=data)
    workflow_id = create_resp.json()["id"]

    resp = await client.post(f"/api/workflows/{workflow_id}/validate")
    assert resp.status_code == 200

    body = resp.json()
    assert body["valid"] is False
    assert len(body["errors"]) > 0


async def test_validate_workflow_not_found(client: AsyncClient):
    """POST /api/workflows/{id}/validate with non-existent id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(f"/api/workflows/{fake_id}/validate")
    assert resp.status_code == 404


async def test_validate_workflow_bad_edge_references(client: AsyncClient):
    """POST /api/workflows/{id}/validate detects edges referencing unknown nodes."""
    data = {
        "name": "Bad Edges Workflow",
        "description": "",
        "graph_definition": {
            "nodes": [
                {"id": "start", "type": "start", "data": {"label": "Start"}},
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "start",
                    "target": "nonexistent",
                },
            ],
        },
    }
    create_resp = await client.post("/api/workflows/", json=data)
    workflow_id = create_resp.json()["id"]

    resp = await client.post(f"/api/workflows/{workflow_id}/validate")
    assert resp.status_code == 200

    body = resp.json()
    assert body["valid"] is False
    # Should detect the invalid edge target
    assert any("nonexistent" in e for e in body["errors"])


async def test_create_workflow_missing_name(client: AsyncClient):
    """POST /api/workflows without required name field returns 422."""
    payload = {
        "description": "Missing name",
        "graph_definition": {},
    }
    resp = await client.post("/api/workflows/", json=payload)
    assert resp.status_code == 422
