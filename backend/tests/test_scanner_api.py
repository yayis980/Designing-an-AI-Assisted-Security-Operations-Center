import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base, get_db
from app.database import models, ai_models, scanner_models

from app.ai.llm_schemas import SecurityAnalysis
from app.ai import scanner_persistence


@pytest.fixture
def client(monkeypatch):
    """Create an isolated test database and API client."""

    monkeypatch.setenv(
        "SOC_API_KEY",
        "test-only-scanner-api-key",
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:

            test_client.headers["X-API-Key"] = (
                "test-only-scanner-api-key"
            )

            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


@pytest.fixture
def sample_finding():
    return {
        "finding_id": "MCP-TEST-001",
        "source": "mcp_runtime",
        "target": "test-mcp-server",
        "tool_name": "get_radio_metrics",
        "category": "behavioral_mismatch",
        "title": "Unexpected filesystem access",
        "description": (
            "An MCP tool attempted to access files "
            "outside its authorized directory."
        ),
        "scanner_severity": "high",
        "evidence": [
            "Sandbox detected unauthorized access attempt."
        ],
    }


def test_create_finding(client, sample_finding):

    response = client.post(
        "/api/v1/scanner/findings",
        json=sample_finding,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["finding_id"] == "MCP-TEST-001"


def test_get_finding(client, sample_finding):

    client.post(
        "/api/v1/scanner/findings",
        json=sample_finding,
    )

    response = client.get(
        "/api/v1/scanner/findings/1"
    )

    assert response.status_code == 200
    assert response.json()["tool_name"] == "get_radio_metrics"


def test_missing_finding(client):

    response = client.get(
        "/api/v1/scanner/findings/999999"
    )

    assert response.status_code == 404


def test_analyze_finding(
    client,
    sample_finding,
    monkeypatch,
):

    client.post(
        "/api/v1/scanner/findings",
        json=sample_finding,
    )

    expected_analysis = SecurityAnalysis(
        event_description="Unauthorized filesystem access",
        threat_type="behavioral_mismatch",
        severity="medium",
        summary="The MCP tool attempted unauthorized access.",
        recommended_actions=[
            "Review tool permissions",
            "Investigate filesystem activity",
        ],
    )

    # Prevent real Gemini API requests
    monkeypatch.setattr(
        scanner_persistence,
        "analyze_scanner_finding",
        lambda finding: expected_analysis,
    )

    response = client.post(
        "/api/v1/scanner/findings/1/analyze"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["ai_severity"] == "medium"
    assert data["finding_db_id"] == 1

    # Verify the result was saved and can be retrieved
    get_response = client.get(
        "/api/v1/scanner/findings/1/analyses"
    )

    assert get_response.status_code == 200

    analyses = get_response.json()

    assert len(analyses) == 1
    assert analyses[0]["summary"] == expected_analysis.summary


def test_gemini_failure(
    client,
    sample_finding,
    monkeypatch,
):

    client.post(
        "/api/v1/scanner/findings",
        json=sample_finding,
    )

    def simulate_failure(finding):
        raise RuntimeError("Gemini unavailable")

    monkeypatch.setattr(
        scanner_persistence,
        "analyze_scanner_finding",
        simulate_failure,
    )

    response = client.post(
        "/api/v1/scanner/findings/1/analyze"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"

    # Original scanner finding must remain available
    finding_response = client.get(
        "/api/v1/scanner/findings/1"
    )

    assert finding_response.status_code == 200




@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"title": ""},
        {"description": "X" * 4001},
        {"evidence": ["Test"] * 21},
        {"evidence": ["X" * 1001]},
    ]
)
def test_invalid_scanner_finding(
    client,
    sample_finding,
    invalid_fields,
):
    """Reject invalid MCP scanner findings."""

    invalid_finding = {
        **sample_finding,
        **invalid_fields,
    }

    response = client.post(
        "/api/v1/scanner/findings",
        json=invalid_finding,
    )

    assert response.status_code == 422

    # Invalid findings must not be saved
    stored = client.get(
        "/api/v1/scanner/findings"
    )

    assert stored.status_code == 200
    assert stored.json() == []


def test_missing_api_key(client, sample_finding):
    """Requests without an API key must be rejected."""

    client.headers.pop("X-API-Key", None)

    response = client.post(
        "/api/v1/scanner/findings",
        json=sample_finding,
    )

    assert response.status_code == 401

    # Verify unauthorized findings were not saved
    client.headers["X-API-Key"] = "test-only-scanner-api-key"

    stored = client.get("/api/v1/scanner/findings")

    assert stored.status_code == 200
    assert stored.json() == []

def test_invalid_api_key(client):
    """Requests with incorrect API keys must be rejected."""

    response = client.get(
        "/api/v1/scanner/findings",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401

def test_missing_server_api_key(client, monkeypatch):
    """Authentication must fail closed when unconfigured."""

    monkeypatch.delenv("SOC_API_KEY", raising=False)

    response = client.get(
        "/api/v1/scanner/findings"
    )

    assert response.status_code == 503

    