"""Shared test fixtures for the AI Agent Orchestration Platform backend tests.

Uses an in-memory SQLite database via aiosqlite so tests run without Docker
or any external services.  A StaticPool is used so that all connections share
the same in-memory database.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db

# Import all models so that Base.metadata knows about every table.
import app.models  # noqa: F401


# ---------------------------------------------------------------------------
# SQLite test engine & session factory
#
# Using StaticPool ensures every connection sees the same in-memory database.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Auto-use fixture: create tables before each test, drop them after
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
async def _setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Database session fixture
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session bound to the test SQLite database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Override the FastAPI get_db dependency
# ---------------------------------------------------------------------------
async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# httpx AsyncClient fixture (uses the real FastAPI app with overridden DB)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx AsyncClient wired to the FastAPI app with test DB."""
    from app.main import app

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_agent_data() -> dict:
    """Return a valid payload for creating an agent via POST /api/agents."""
    return {
        "name": "Test Agent",
        "role": "assistant",
        "system_prompt": "You are a helpful test assistant.",
        "model": "gpt-4o-mini",
        "tools": ["calculator"],
        "channels": [],
        "memory_enabled": True,
        "memory_window": 20,
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "temperature": 0.7,
        "max_tokens": 4096,
    }


@pytest.fixture
def sample_workflow_data() -> dict:
    """Return a valid payload for creating a workflow with a simple 2-node graph."""
    return {
        "name": "Test Workflow",
        "description": "A workflow used for testing",
        "is_template": False,
        "graph_definition": {
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": "Start"},
                },
                {
                    "id": "end",
                    "type": "end",
                    "position": {"x": 0, "y": 200},
                    "data": {"label": "End"},
                },
            ],
            "edges": [
                {
                    "id": "e-start-end",
                    "source": "start",
                    "target": "end",
                    "type": "default",
                },
            ],
        },
    }
