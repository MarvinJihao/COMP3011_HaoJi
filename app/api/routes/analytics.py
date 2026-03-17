from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.disaster_event import (
    event_counts_by_severity,
    event_counts_by_source,
    event_counts_by_type,
    total_events,
)
from app.db.session import get_db
from app.models.disaster_event import DisasterEvent
from app.schemas.analytics import (
    AnalyticsDailySeriesRead,
    AnalyticsHotspotsRead,
    AnalyticsSummaryRead,
    EventRiskListRead,
)

router = APIRouter()

TYPE_RISK_WEIGHT = {
    "wildfire": 25.0,
    "earthquake": 30.0,
    "volcano": 28.0,
}


def _to_datetime_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[datetime | None, datetime | None]:
    start_time = (
        datetime.combine(start_date, time.min).replace(tzinfo=None)
        if start_date
        else None
    )
    end_time = (
        datetime.combine(end_date, time.max).replace(tzinfo=None)
        if end_date
        else None
    )
    return start_time, end_time


def _event_risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _score_event(event: DisasterEvent, nearby_count: int, now: datetime) -> dict:
    age_days = max((now - event.event_time).total_seconds() / 86400, 0.0)
    recency_score = max(0.0, 25.0 - min(age_days, 10.0) * 2.5)
    severity_score = float(event.severity) * 8.0
    type_score = TYPE_RISK_WEIGHT.get(event.event_type, 20.0)
    density_score = min(max(nearby_count - 1, 0) * 6.0, 20.0)
    total = round(severity_score + type_score + recency_score + density_score, 2)

    return {
        "event_id": event.id,
        "title": event.title,
        "type": event.event_type,
        "source": event.source,
        "severity": event.severity,
        "event_time": event.event_time,
        "risk_score": total,
        "risk_level": _event_risk_level(total),
        "factors": {
            "severity": round(severity_score, 2),
            "type_weight": round(type_score, 2),
            "recency": round(recency_score, 2),
            "local_density": round(density_score, 2),
        },
    }


@router.get("/analytics/summary", response_model=AnalyticsSummaryRead)
def analytics_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    latest = db.query(func.max(DisasterEvent.event_time)).scalar()
    oldest = db.query(func.min(DisasterEvent.event_time)).scalar()
    total = total_events(db, start_time=start_time, end_time=end_time)

    by_type = event_counts_by_type(db, start_time=start_time, end_time=end_time)
    by_source = event_counts_by_source(db, start_time=start_time, end_time=end_time)
    by_severity = event_counts_by_severity(db, start_time=start_time, end_time=end_time)

    return {
        "total_events": total,
        "time_range": {
            "start_date": start_date,
            "end_date": end_date,
            "oldest_event_time": oldest,
            "latest_event_time": latest,
        },
        "by_type": [{"type": t, "count": c} for t, c in by_type],
        "by_source": [{"source": s, "count": c} for s, c in by_source],
        "by_severity": [{"severity": s, "count": c} for s, c in by_severity],
    }


@router.get("/analytics/timeseries/daily", response_model=AnalyticsDailySeriesRead)
def analytics_daily_timeseries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    query = db.query(func.date(DisasterEvent.event_time), func.count(DisasterEvent.id)).group_by(
        func.date(DisasterEvent.event_time)
    )
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)

    rows = query.order_by(func.date(DisasterEvent.event_time).asc()).all()
    return {"series": [{"date": d, "count": c} for d, c in rows]}


@router.get("/analytics/hotspots", response_model=AnalyticsHotspotsRead)
def analytics_hotspots(
    precision: int = Query(default=1, ge=0, le=3),
    top_n: int = Query(default=10, ge=1, le=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    lat_bucket = func.round(DisasterEvent.latitude, precision)
    lon_bucket = func.round(DisasterEvent.longitude, precision)

    query = db.query(
        lat_bucket.label("lat"),
        lon_bucket.label("lon"),
        func.count(DisasterEvent.id).label("count"),
    )
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)

    rows = (
        query.group_by(lat_bucket, lon_bucket)
        .order_by(func.count(DisasterEvent.id).desc())
        .limit(top_n)
        .all()
    )
    return {"hotspots": [{"latitude": la, "longitude": lo, "count": c} for la, lo, c in rows]}


@router.get("/analytics/risk-assessment", response_model=EventRiskListRead)
def analytics_risk_assessment(
    days: int = Query(default=30, ge=1, le=365),
    top_n: int = Query(default=10, ge=1, le=100),
    event_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    start_time = now.replace(microsecond=0) - timedelta(days=days)

    query = db.query(DisasterEvent).filter(DisasterEvent.event_time >= start_time)
    if event_type:
        query = query.filter(DisasterEvent.event_type == event_type)

    events = query.order_by(DisasterEvent.event_time.desc()).all()
    if not events:
        return {"items": []}

    grouped_counts: dict[tuple[float, float], int] = {}
    for event in events:
        key = (round(event.latitude, 1), round(event.longitude, 1))
        grouped_counts[key] = grouped_counts.get(key, 0) + 1

    scored = []
    for event in events:
        key = (round(event.latitude, 1), round(event.longitude, 1))
        scored.append(_score_event(event, grouped_counts[key], now))

    scored.sort(key=lambda item: item["risk_score"], reverse=True)
    return {"items": scored[:top_n]}
