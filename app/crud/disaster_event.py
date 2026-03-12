from datetime import datetime
from typing import Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.disaster_event import DisasterEvent
from app.models.source_metadata import SourceMetadata
from app.schemas.disaster_event import DisasterEventCreate, DisasterEventUpdate


def get_or_create_source(
    db: Session,
    *,
    source_key: str,
    provider: str,
    title: Optional[str] = None,
    source_url: Optional[str] = None,
    description: Optional[str] = None,
) -> SourceMetadata:
    source = (
        db.query(SourceMetadata)
        .filter(SourceMetadata.source_key == source_key)
        .first()
    )
    if source:
        updated = False
        if source.provider != provider:
            source.provider = provider
            updated = True
        if title and source.title != title:
            source.title = title
            updated = True
        if source_url and source.source_url != source_url:
            source.source_url = source_url
            updated = True
        if description and source.description != description:
            source.description = description
            updated = True
        if updated:
            db.add(source)
            db.commit()
            db.refresh(source)
        return source

    source = SourceMetadata(
        source_key=source_key,
        title=title or source_key,
        provider=provider,
        source_url=source_url,
        description=description,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def list_sources(db: Session) -> list[SourceMetadata]:
    return db.query(SourceMetadata).order_by(SourceMetadata.provider, SourceMetadata.source_key).all()


def get_disaster_event(db: Session, event_id: int) -> Optional[DisasterEvent]:
    return (
        db.query(DisasterEvent)
        .options(joinedload(DisasterEvent.source_metadata))
        .filter(DisasterEvent.id == event_id)
        .first()
    )


def list_disaster_events(
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
) -> list[DisasterEvent]:
    query = db.query(DisasterEvent).options(joinedload(DisasterEvent.source_metadata))

    if source:
        query = query.join(DisasterEvent.source_metadata).filter(SourceMetadata.source_key == source)
    if type:
        query = query.filter(DisasterEvent.event_type == type)
    if severity_min is not None:
        query = query.filter(DisasterEvent.severity >= severity_min)
    if severity_max is not None:
        query = query.filter(DisasterEvent.severity <= severity_max)
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)
    if min_lat is not None:
        query = query.filter(DisasterEvent.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(DisasterEvent.latitude <= max_lat)
    if min_lon is not None:
        query = query.filter(DisasterEvent.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(DisasterEvent.longitude <= max_lon)

    return query.order_by(DisasterEvent.event_time.desc()).offset(skip).limit(limit).all()


def create_disaster_event(
    db: Session,
    payload: DisasterEventCreate,
    *,
    source_provider: str = "manual",
) -> DisasterEvent:
    source = get_or_create_source(
        db,
        source_key=payload.source,
        provider=source_provider,
        title=payload.source,
    )
    event = DisasterEvent(
        title=payload.title,
        event_type=payload.type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        severity=payload.severity,
        source_id=source.id,
        external_id=payload.external_id,
        event_time=payload.event_time,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return get_disaster_event(db, event.id)


def update_disaster_event(
    db: Session,
    db_event: DisasterEvent,
    payload: Union[DisasterEventCreate, DisasterEventUpdate],
    *,
    partial: bool = False,
    source_provider: str = "manual",
) -> DisasterEvent:
    update_data = payload.model_dump(exclude_unset=partial)

    if "source" in update_data and update_data["source"] is not None:
        source = get_or_create_source(
            db,
            source_key=update_data.pop("source"),
            provider=source_provider,
        )
        db_event.source_id = source.id

    if "type" in update_data and update_data["type"] is not None:
        db_event.event_type = update_data.pop("type")

    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return get_disaster_event(db, db_event.id)


def delete_disaster_event(db: Session, db_event: DisasterEvent) -> None:
    db.delete(db_event)
    db.commit()


def find_existing_event(
    db: Session,
    *,
    title: str,
    event_time: datetime,
    source: str,
) -> Optional[DisasterEvent]:
    return (
        db.query(DisasterEvent)
        .join(DisasterEvent.source_metadata)
        .options(joinedload(DisasterEvent.source_metadata))
        .filter(
            DisasterEvent.title == title,
            DisasterEvent.event_time == event_time,
            SourceMetadata.source_key == source,
        )
        .first()
    )


def event_counts_by_type(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[str, int]]:
    query = db.query(DisasterEvent.event_type, func.count(DisasterEvent.id))
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)
    return (
        query.group_by(DisasterEvent.event_type)
        .order_by(func.count(DisasterEvent.id).desc())
        .all()
    )


def event_counts_by_source(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[str, int]]:
    query = db.query(SourceMetadata.source_key, func.count(DisasterEvent.id)).join(
        DisasterEvent.source_metadata
    )
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)
    return (
        query.group_by(SourceMetadata.source_key)
        .order_by(func.count(DisasterEvent.id).desc())
        .all()
    )


def event_counts_by_severity(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[tuple[int, int]]:
    query = db.query(DisasterEvent.severity, func.count(DisasterEvent.id))
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)
    return query.group_by(DisasterEvent.severity).order_by(DisasterEvent.severity.asc()).all()


def total_events(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> int:
    query = db.query(func.count(DisasterEvent.id))
    if start_time:
        query = query.filter(DisasterEvent.event_time >= start_time)
    if end_time:
        query = query.filter(DisasterEvent.event_time <= end_time)
    return query.scalar() or 0
