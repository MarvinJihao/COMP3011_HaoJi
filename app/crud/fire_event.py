from typing import Optional, Union


from sqlalchemy.orm import Session

from app.models.fire_event import FireEvent
from app.schemas.fire_event import FireEventCreate, FireEventUpdate


def get_fire_event(db: Session, event_id: int) -> Optional[FireEvent]:
    return db.query(FireEvent).filter(FireEvent.id == event_id).first()

def list_fire_events(db: Session, skip: int = 0, limit: int = 100) -> list[FireEvent]:
    return db.query(FireEvent).offset(skip).limit(limit).all()


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
