from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.fire_event import FireEvent


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
    return TestClient(app), TestingSessionLocal


def test_create_and_filter_fire_events():
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

    r1 = client.post("/fire-events", json=payload_1)
    r2 = client.post("/fire-events", json=payload_2)
    assert r1.status_code == 201
    assert r2.status_code == 201

    res = client.get("/fire-events", params={"source": "EO", "severity_min": 2, "severity_max": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Fire B"


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

    db = SessionLocal()
    try:
        count = db.query(FireEvent).count()
        assert count == 1
        event = db.query(FireEvent).first()
        assert event.title == "Wildfire Mock 1"
        assert event.source == "InciWeb"
        assert event.event_time.date().isoformat() == "2026-03-01"
    finally:
        db.close()
