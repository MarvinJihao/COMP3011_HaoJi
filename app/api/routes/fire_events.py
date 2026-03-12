from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.crud.disaster_event import (
    create_disaster_event,
    delete_disaster_event,
    get_disaster_event,
    list_disaster_events,
    update_disaster_event,
)
from app.db.session import get_db
from app.schemas.disaster_event import (
    DisasterEventCreate,
    DisasterEventRead,
    DisasterEventUpdate,
)

router = APIRouter()


@router.post(
    "/events",
    response_model=DisasterEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event_endpoint(
    payload: DisasterEventCreate,
    db: Session = Depends(get_db),
):
    return create_disaster_event(db, payload)


@router.get("/events", response_model=list[DisasterEventRead])
def list_events_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    severity_min: int | None = Query(default=None, ge=1, le=5),
    severity_max: int | None = Query(default=None, ge=1, le=5),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    min_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lon: float | None = Query(default=None, ge=-180, le=180),
    max_lon: float | None = Query(default=None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    return list_disaster_events(
        db,
        skip=skip,
        limit=limit,
        type=type,
        source=source,
        severity_min=severity_min,
        severity_max=severity_max,
        start_time=start_time,
        end_time=end_time,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )


@router.get("/events/{event_id}", response_model=DisasterEventRead)
def get_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_disaster_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.put("/events/{event_id}", response_model=DisasterEventRead)
def replace_event_endpoint(
    event_id: int,
    payload: DisasterEventCreate,
    db: Session = Depends(get_db),
):
    event = get_disaster_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return update_disaster_event(db, event, payload, partial=False)


@router.patch("/events/{event_id}", response_model=DisasterEventRead)
def patch_event_endpoint(
    event_id: int,
    payload: DisasterEventUpdate,
    db: Session = Depends(get_db),
):
    event = get_disaster_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return update_disaster_event(db, event, payload, partial=True)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_disaster_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    delete_disaster_event(db, event)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
