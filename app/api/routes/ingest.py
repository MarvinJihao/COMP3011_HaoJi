from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.fire_event import create_fire_event, find_existing_event
from app.db.session import get_db
from app.schemas.fire_event import FireEventCreate

router = APIRouter()

EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"


def _parse_event_time(geometry: list[dict[str, Any]]) -> datetime:
    if not geometry:
        return datetime.now(timezone.utc)
    newest = geometry[-1].get("date")
    if not newest:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(newest.replace("Z", "+00:00"))
    # Store as naive UTC to keep SQLite comparisons consistent.
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _extract_point(geometry: list[dict[str, Any]]) -> tuple[float, float]:
    if not geometry:
        raise ValueError("Event has no geometry")

    latest = geometry[-1]
    coords = latest.get("coordinates")
    if not coords:
        raise ValueError("Event geometry has no coordinates")

    geometry_type = latest.get("type")

    # Point: [lon, lat]
    if geometry_type == "Point" or isinstance(coords[0], (int, float)):
        lon, lat = coords[0], coords[1]
    # Polygon: [[[lon, lat], ...], ...]
    elif geometry_type == "Polygon":
        lon, lat = coords[0][0][0], coords[0][0][1]
    else:
        # Fallback for unexpected structures.
        lon, lat = coords[0][0], coords[0][1]
    return float(lat), float(lon)


def _severity_from_magnitude(magnitude_value: Any) -> int:
    if magnitude_value is None:
        return 3
    try:
        value = float(magnitude_value)
    except (TypeError, ValueError):
        return 3
    if value < 10:
        return 1
    if value < 50:
        return 2
    if value < 100:
        return 3
    if value < 200:
        return 4
    return 5


@router.post(
    "/ingest/eonet/wildfires/sync",
    status_code=status.HTTP_200_OK,
)
def sync_eonet_wildfires(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=200, ge=1, le=1000),
    status_filter: str = Query(default="open", pattern="^(open|closed|all)$"),
    db: Session = Depends(get_db),
):
    params = {
        "category": "wildfires",
        "days": days,
        "limit": limit,
        "status": status_filter,
    }

    try:
        response = httpx.get(EONET_EVENTS_URL, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch NASA EONET data: {exc}",
        ) from exc

    events = payload.get("events", [])
    inserted = 0
    skipped = 0
    failed = 0

    for item in events:
        try:
            title = item.get("title") or "Untitled wildfire event"
            geometry = item.get("geometry") or []
            lat, lon = _extract_point(geometry)
            event_time = _parse_event_time(geometry)
            source_list = item.get("sources") or []
            source_id = source_list[0].get("id") if source_list else "NASA-EONET"
            severity = _severity_from_magnitude(item.get("magnitudeValue"))

            existing = find_existing_event(
                db,
                title=title,
                event_time=event_time,
                source=source_id,
            )
            if existing:
                skipped += 1
                continue

            create_fire_event(
                db,
                FireEventCreate(
                    title=title,
                    type="wildfire",
                    latitude=lat,
                    longitude=lon,
                    severity=severity,
                    source=source_id,
                    event_time=event_time,
                ),
            )
            inserted += 1
        except Exception:
            failed += 1

    return {
        "provider": "NASA EONET v3",
        "category": "wildfires",
        "requested": len(events),
        "inserted": inserted,
        "skipped_existing": skipped,
        "failed": failed,
        "filters": params,
    }


@router.get("/ingest/eonet/wildfires/preview")
def preview_eonet_wildfires(
    days: int = Query(default=7, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=200),
    status_filter: str = Query(default="open", pattern="^(open|closed|all)$"),
):
    params = {
        "category": "wildfires",
        "days": days,
        "limit": limit,
        "status": status_filter,
    }

    try:
        response = httpx.get(EONET_EVENTS_URL, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch NASA EONET data: {exc}",
        ) from exc

    samples = []
    for item in payload.get("events", []):
        geometry = item.get("geometry") or []
        try:
            lat, lon = _extract_point(geometry)
        except Exception:
            lat, lon = None, None
        sources = item.get("sources") or []
        samples.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "event_time": _parse_event_time(geometry),
                "latitude": lat,
                "longitude": lon,
                "source": sources[0].get("id") if sources else None,
            }
        )
    return {"count": len(samples), "events": samples}
