import base64

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


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
    return client


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
    return TestClient(app)


def _seed_data(client: TestClient):
    records = [
        {
            "title": "A",
            "type": "wildfire",
            "latitude": 30.0,
            "longitude": -110.0,
            "severity": 2,
            "source": "InciWeb",
            "event_time": "2026-03-01T10:00:00",
        },
        {
            "title": "B",
            "type": "wildfire",
            "latitude": 30.1,
            "longitude": -110.1,
            "severity": 4,
            "source": "EO",
            "event_time": "2026-03-01T12:00:00",
        },
        {
            "title": "C",
            "type": "volcano",
            "latitude": 10.0,
            "longitude": 120.0,
            "severity": 3,
            "source": "EO",
            "event_time": "2026-03-02T08:00:00",
        },
    ]
    for item in records:
        r = client.post("/events", json=item)
        assert r.status_code == 201


def test_analytics_requires_basic_auth():
    client = _build_plain_client()
    response = client.get("/analytics/summary")
    assert response.status_code == 401


def test_analytics_summary_and_timeseries():
    client = _build_client()
    _seed_data(client)

    summary = client.get("/analytics/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_events"] == 3

    by_type = {x["type"]: x["count"] for x in body["by_type"]}
    assert by_type["wildfire"] == 2
    assert by_type["volcano"] == 1

    daily = client.get("/analytics/timeseries/daily")
    assert daily.status_code == 200
    series = daily.json()["series"]
    assert len(series) == 2
    assert series[0]["date"] == "2026-03-01"
    assert series[0]["count"] == 2


def test_analytics_hotspots():
    client = _build_client()
    _seed_data(client)

    response = client.get("/analytics/hotspots", params={"precision": 1, "top_n": 2})
    assert response.status_code == 200
    hotspots = response.json()["hotspots"]
    assert len(hotspots) >= 1
    assert hotspots[0]["count"] >= 1


def test_analytics_summary_respects_date_filters():
    client = _build_client()
    _seed_data(client)

    response = client.get(
        "/analytics/summary",
        params={"start_date": "2026-03-02", "end_date": "2026-03-02"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["total_events"] == 1
    assert body["by_type"] == [{"type": "volcano", "count": 1}]
    assert body["by_source"] == [{"source": "EO", "count": 1}]
    assert body["by_severity"] == [{"severity": 3, "count": 1}]


def test_analytics_hotspots_with_controlled_fixture_returns_expected_clusters():
    client = _build_client()

    records = [
        {
            "title": "Cluster 1A",
            "type": "wildfire",
            "latitude": 35.14,
            "longitude": -120.14,
            "severity": 2,
            "source": "InciWeb",
            "event_time": "2026-03-03T10:00:00",
        },
        {
            "title": "Cluster 1B",
            "type": "wildfire",
            "latitude": 35.11,
            "longitude": -120.11,
            "severity": 3,
            "source": "InciWeb",
            "event_time": "2026-03-03T11:00:00",
        },
        {
            "title": "Cluster 2",
            "type": "earthquake",
            "latitude": 10.01,
            "longitude": 100.01,
            "severity": 4,
            "source": "us",
            "event_time": "2026-03-04T11:00:00",
        },
    ]
    for item in records:
        r = client.post("/events", json=item)
        assert r.status_code == 201

    response = client.get("/analytics/hotspots", params={"precision": 1, "top_n": 2})
    assert response.status_code == 200
    hotspots = response.json()["hotspots"]

    assert hotspots[0]["latitude"] == 35.1
    assert hotspots[0]["longitude"] == -120.1
    assert hotspots[0]["count"] == 2
    assert hotspots[1]["count"] == 1


def test_analytics_timeseries_respects_date_filters():
    client = _build_client()
    _seed_data(client)

    response = client.get(
        "/analytics/timeseries/daily",
        params={"start_date": "2026-03-01", "end_date": "2026-03-01"},
    )
    assert response.status_code == 200
    assert response.json()["series"] == [{"date": "2026-03-01", "count": 2}]
