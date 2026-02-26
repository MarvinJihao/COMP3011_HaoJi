from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.crud.fire_event import (
    create_fire_event,
    delete_fire_event,
    get_fire_event,
    list_fire_events,
    update_fire_event,
)
from app.db.session import get_db
from app.schemas.fire_event import FireEventCreate, FireEventRead, FireEventUpdate

router = APIRouter()


@router.post(
    "/fire-events",
    response_model=FireEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_fire_event_endpoint(
    payload: FireEventCreate,
    db: Session = Depends(get_db),
):
    return create_fire_event(db, payload)


@router.get("/fire-events", response_model=list[FireEventRead])
def list_fire_events_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_fire_events(db, skip=skip, limit=limit)


@router.get("/fire-events/{event_id}", response_model=FireEventRead)
def get_fire_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_fire_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fire event not found")
    return event


@router.put("/fire-events/{event_id}", response_model=FireEventRead)
def replace_fire_event_endpoint(
    event_id: int,
    payload: FireEventCreate,
    db: Session = Depends(get_db),
):
    event = get_fire_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fire event not found")
    return update_fire_event(db, event, payload, partial=False)


@router.patch("/fire-events/{event_id}", response_model=FireEventRead)
def patch_fire_event_endpoint(
    event_id: int,
    payload: FireEventUpdate,
    db: Session = Depends(get_db),
):
    event = get_fire_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fire event not found")
    return update_fire_event(db, event, payload, partial=True)


@router.delete("/fire-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fire_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_fire_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fire event not found")
    delete_fire_event(db, event)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
