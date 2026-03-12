import base64

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.disaster_event import DisasterEvent


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    token = base64.b64encode(b"admin:admin123").decode("ascii")
    client.headers.update({"Authorization": f"Basic {token}"})
    return client, TestingSessionLocal


def _build_plain_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def test_create_and_filter_events():
    client, _ = _build_client()

    payload_1 = {
        "title": "Fire A",
        "type": "wildfire",
        "latitude": 35.1,
        "longitude": -118.2,
        "severity": 4,
        "source": "InciWeb",
        "event_time": "2026-02-01T12:00:00",
    }
    payload_2 = {
        "title": "Fire B",
        "type": "wildfire",
        "latitude": 40.1,
        "longitude": -120.2,
        "severity": 2,
        "source": "EO",
        "event_time": "2026-02-10T12:00:00",
    }

    r1 = client.post("/events", json=payload_1)
    r2 = client.post("/events", json=payload_2)
    assert r1.status_code == 201
    assert r2.status_code == 201

    res = client.get("/events", params={"source": "EO", "severity_min": 2, "severity_max": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Fire B"


def test_protected_endpoint_requires_basic_auth():
    client, _ = _build_plain_client()

    response = client.get("/events")
    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_basic_auth():
    client, _ = _build_plain_client()
    bad_token = base64.b64encode(b"admin:wrong-password").decode("ascii")
    client.headers.update({"Authorization": f"Basic {bad_token}"})

    response = client.get("/events")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid basic authentication credentials"


def test_health_endpoint_is_public():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health_failure_returns_503():
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("db unavailable")

    def override_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database connection failed"


def test_create_event_invalid_payload_returns_422():
    client, _ = _build_client()

    payload = {
        "title": "",
        "type": "wildfire",
        "latitude": 120.0,
        "longitude": -118.25,
        "severity": 9,
        "source": "manual",
        "event_time": "2026-03-12T10:00:00",
    }

    response = client.post("/events", json=payload)
    assert response.status_code == 422


def test_create_event_boundary_values_are_accepted():
    client, _ = _build_client()

    low_payload = {
        "title": "Boundary Low",
        "type": "wildfire",
        "latitude": -90,
        "longitude": -180,
        "severity": 1,
        "source": "manual",
        "event_time": "2026-03-12T00:00:00",
    }
    high_payload = {
        "title": "Boundary High",
        "type": "earthquake",
        "latitude": 90,
        "longitude": 180,
        "severity": 5,
        "source": "manual",
        "event_time": "2026-03-12T23:59:59",
    }

    low_response = client.post("/events", json=low_payload)
    high_response = client.post("/events", json=high_payload)

    assert low_response.status_code == 201
    assert high_response.status_code == 201
    assert low_response.json()["severity"] == 1
    assert high_response.json()["severity"] == 5


def test_sync_eonet_wildfires_with_mock(monkeypatch):
    client, SessionLocal = _build_client()

    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "events": [
                    {
                        "id": "EONET_1",
                        "title": "Wildfire Mock 1",
                        "sources": [{"id": "InciWeb"}],
                        "geometry": [
                            {"date": "2026-03-01T00:00:00Z", "coordinates": [-120.0, 40.0]}
                        ],
                        "magnitudeValue": 120,
                    }
                ]
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("app.api.routes.ingest.httpx.get", mock_get)
    response = client.post("/ingest/eonet/wildfires/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 1

    sources_response = client.get("/sources")
    assert sources_response.status_code == 200
    assert sources_response.json()[0]["source_key"] == "InciWeb"

    runs_response = client.get("/ingest/runs")
    assert runs_response.status_code == 200
    assert runs_response.json()[0]["provider"] == "NASA EONET v3"

    db = SessionLocal()
    try:
        count = db.query(DisasterEvent).count()
        assert count == 1
        event = db.query(DisasterEvent).first()
        assert event.title == "Wildfire Mock 1"
        assert event.source == "InciWeb"
        assert event.event_time.date().isoformat() == "2026-03-01"
    finally:
        db.close()


def test_duplicate_eonet_ingest_is_skipped(monkeypatch):
    client, SessionLocal = _build_client()

    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "events": [
                    {
                        "id": "EONET_DUP",
                        "title": "Duplicate Wildfire",
                        "sources": [{"id": "InciWeb"}],
                        "geometry": [
                            {"date": "2026-03-02T00:00:00Z", "coordinates": [-121.0, 41.0]}
                        ],
                        "magnitudeValue": 50,
                    }
                ]
            }

    monkeypatch.setattr("app.api.routes.ingest.httpx.get", lambda *args, **kwargs: MockResponse())

    first = client.post("/ingest/eonet/wildfires/sync")
    second = client.post("/ingest/eonet/wildfires/sync")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["inserted"] == 1
    assert second.json()["inserted"] == 0
    assert second.json()["skipped_existing"] == 1

    db = SessionLocal()
    try:
        assert db.query(DisasterEvent).count() == 1
    finally:
        db.close()


def test_eonet_ingest_upstream_failure_returns_502_and_records_failed_run(monkeypatch):
    client, _ = _build_client()

    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr("app.api.routes.ingest.httpx.get", failing_get)

    response = client.post("/ingest/eonet/wildfires/sync")
    assert response.status_code == 502

    runs_response = client.get("/ingest/runs")
    assert runs_response.status_code == 200
    latest_run = runs_response.json()[0]
    assert latest_run["status"] == "failed"
    assert latest_run["provider"] == "NASA EONET v3"


def test_sync_usgs_earthquakes_with_mock(monkeypatch):
    client, SessionLocal = _build_client()

    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "features": [
                    {
                        "id": "us7000mock",
                        "properties": {
                            "title": "M 4.5 - Test Region",
                            "place": "Test Region",
                            "mag": 4.5,
                            "net": "us",
                            "time": 1772409600000,
                        },
                        "geometry": {"type": "Point", "coordinates": [120.5, 23.5, 10.0]},
                    }
                ]
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("app.api.routes.ingest.httpx.get", mock_get)
    response = client.post("/ingest/usgs/earthquakes/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 1

    db = SessionLocal()
    try:
        event = db.query(DisasterEvent).first()
        assert event is not None
        assert event.type == "earthquake"
        assert event.source == "us"
        assert event.latitude == 23.5
        assert event.longitude == 120.5
    finally:
        db.close()


def test_usgs_ingest_upstream_failure_returns_502(monkeypatch):
    client, _ = _build_client()

    def failing_get(*args, **kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr("app.api.routes.ingest.httpx.get", failing_get)

    response = client.post("/ingest/usgs/earthquakes/sync")
    assert response.status_code == 502
    assert "Failed to fetch USGS Earthquake data" in response.json()["detail"]
