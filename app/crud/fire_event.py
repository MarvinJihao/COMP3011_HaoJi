from datetime import datetime
from typing import Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.fire_event import FireEvent
from app.schemas.fire_event import FireEventCreate, FireEventUpdate


def get_fire_event(db: Session, event_id: int) -> Optional[FireEvent]:
    return db.query(FireEvent).filter(FireEvent.id == event_id).first()


def list_fire_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    *,
    type: Optional[str] = None,
    source: Optional[str] = None,
    severity_min: Optional[int] = None,
    severity_max: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
) -> list[FireEvent]:
    query = db.query(FireEvent)

    if type:
        query = query.filter(FireEvent.type == type)
    if source:
        query = query.filter(FireEvent.source == source)
    if severity_min is not None:
        query = query.filter(FireEvent.severity >= severity_min)
    if severity_max is not None:
        query = query.filter(FireEvent.severity <= severity_max)
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)
    if min_lat is not None:
        query = query.filter(FireEvent.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(FireEvent.latitude <= max_lat)
    if min_lon is not None:
        query = query.filter(FireEvent.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(FireEvent.longitude <= max_lon)

    return query.order_by(FireEvent.event_time.desc()).offset(skip).limit(limit).all()


def create_fire_event(db: Session, payload: FireEventCreate) -> FireEvent:
    event = FireEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_fire_event(
    db: Session,
    db_event: FireEvent,
    payload: Union[FireEventCreate, FireEventUpdate],
    *,
    partial: bool = False,
) -> FireEvent:
    update_data = payload.model_dump(exclude_unset=partial)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_fire_event(db: Session, db_event: FireEvent) -> None:
    db.delete(db_event)
    db.commit()


def find_existing_event(
    db: Session,
    *,
    title: str,
    event_time: datetime,
    source: str,
) -> Optional[FireEvent]:
    return (
        db.query(FireEvent)
        .filter(
            FireEvent.title == title,
            FireEvent.event_time == event_time,
            FireEvent.source == source,
        )
        .first()
    )


def event_counts_by_type(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[str, int]]:
    query = db.query(FireEvent.type, func.count(FireEvent.id))
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)
    return query.group_by(FireEvent.type).order_by(func.count(FireEvent.id).desc()).all()


def event_counts_by_source(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[str, int]]:
    query = db.query(FireEvent.source, func.count(FireEvent.id))
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)
    return query.group_by(FireEvent.source).order_by(func.count(FireEvent.id).desc()).all()


def event_counts_by_severity(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[int, int]]:
    query = db.query(FireEvent.severity, func.count(FireEvent.id))
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)
    return query.group_by(FireEvent.severity).order_by(FireEvent.severity.asc()).all()


def total_events(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> int:
    query = db.query(func.count(FireEvent.id))
    if start_time:
        query = query.filter(FireEvent.event_time >= start_time)
    if end_time:
        query = query.filter(FireEvent.event_time <= end_time)
    return query.scalar() or 0
