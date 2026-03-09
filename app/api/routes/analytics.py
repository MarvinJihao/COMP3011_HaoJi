from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.fire_event import (
    event_counts_by_severity,
    event_counts_by_source,
    event_counts_by_type,
    total_events,
)
from app.db.session import get_db
from app.models.fire_event import FireEvent

router = APIRouter()


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


@router.get("/analytics/summary")
def analytics_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    latest = db.query(func.max(FireEvent.event_time)).scalar()
    oldest = db.query(func.min(FireEvent.event_time)).scalar()
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


@router.get("/analytics/timeseries/daily")
def analytics_daily_timeseries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    query = db.query(func.date(FireEvent.event_time), func.count(FireEvent.id)).group_by(
        func.date(FireEvent.event_time)
    )
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)

    rows = query.order_by(func.date(FireEvent.event_time).asc()).all()
    return {"series": [{"date": d, "count": c} for d, c in rows]}


@router.get("/analytics/hotspots")
def analytics_hotspots(
    precision: int = Query(default=1, ge=0, le=3),
    top_n: int = Query(default=10, ge=1, le=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start_time, end_time = _to_datetime_range(start_date, end_date)

    lat_bucket = func.round(FireEvent.latitude, precision)
    lon_bucket = func.round(FireEvent.longitude, precision)

    query = db.query(
        lat_bucket.label("lat"),
        lon_bucket.label("lon"),
        func.count(FireEvent.id).label("count"),
    )
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)

    rows = (
        query.group_by(lat_bucket, lon_bucket)
        .order_by(func.count(FireEvent.id).desc())
        .limit(top_n)
        .all()
    )
    return {"hotspots": [{"latitude": la, "longitude": lo, "count": c} for la, lo, c in rows]}
