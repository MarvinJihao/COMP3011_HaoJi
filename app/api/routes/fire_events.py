from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.fire_event import FireEvent

router = APIRouter()


@router.post("/fire-events")
def create_fire_event(db: Session = Depends(get_db)):
    event = FireEvent(
        title="Test Fire",
        type="wildfire",
        latitude=10.0,
        longitude=20.0,
        severity=3,
        source="manual",
        event_time=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event