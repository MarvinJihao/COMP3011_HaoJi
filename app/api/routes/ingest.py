from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.disaster_event import (
    create_disaster_event,
    find_existing_event,
    list_sources,
)
from app.crud.ingest_run import complete_ingest_run, create_ingest_run, list_ingest_runs
from app.db.session import get_db
from app.schemas.disaster_event import DisasterEventCreate
from app.schemas.ingest_run import IngestRunRead
from app.schemas.source_metadata import SourceMetadataRead

router = APIRouter()

EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
USGS_QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


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


def _severity_from_earthquake_mag(mag: Any) -> int:
    if mag is None:
        return 2
    try:
        value = float(mag)
    except (TypeError, ValueError):
        return 2
    if value < 2.5:
        return 1
    if value < 4.0:
        return 2
    if value < 5.5:
        return 3
    if value < 7.0:
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
    run = create_ingest_run(
        db,
        provider="NASA EONET v3",
        dataset="wildfires",
        filters=params,
    )

    try:
        response = httpx.get(EONET_EVENTS_URL, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        complete_ingest_run(
            db,
            run,
            status="failed",
            requested_count=0,
            inserted_count=0,
            skipped_count=0,
            failed_count=0,
            message=str(exc),
        )
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

            create_disaster_event(
                db,
                DisasterEventCreate(
                    title=title,
                    type="wildfire",
                    latitude=lat,
                    longitude=lon,
                    severity=severity,
                    source=source_id,
                    external_id=item.get("id"),
                    event_time=event_time,
                ),
                source_provider="NASA EONET v3",
            )
            inserted += 1
        except Exception:
            failed += 1

    complete_ingest_run(
        db,
        run,
        status="completed",
        requested_count=len(events),
        inserted_count=inserted,
        skipped_count=skipped,
        failed_count=failed,
    )

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


@router.post(
    "/ingest/usgs/earthquakes/sync",
    status_code=status.HTTP_200_OK,
)
def sync_usgs_earthquakes(
    days: int = Query(default=30, ge=1, le=365),
    min_magnitude: float = Query(default=2.5, ge=-1, le=10),
    limit: int = Query(default=500, ge=1, le=20000),
    db: Session = Depends(get_db),
):
    end_time = datetime.now(timezone.utc)
    start_time = end_time.replace(microsecond=0) - timedelta(days=days)

    params = {
        "format": "geojson",
        "starttime": start_time.isoformat().replace("+00:00", "Z"),
        "endtime": end_time.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "minmagnitude": min_magnitude,
        "limit": limit,
        "orderby": "time",
    }
    run = create_ingest_run(
        db,
        provider="USGS FDSN Event API",
        dataset="earthquakes",
        filters=params,
    )

    try:
        response = httpx.get(USGS_QUERY_URL, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        complete_ingest_run(
            db,
            run,
            status="failed",
            requested_count=0,
            inserted_count=0,
            skipped_count=0,
            failed_count=0,
            message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch USGS Earthquake data: {exc}",
        ) from exc

    features = payload.get("features", [])
    inserted = 0
    skipped = 0
    failed = 0

    for item in features:
        try:
            properties = item.get("properties") or {}
            geometry = item.get("geometry") or {}
            coordinates = geometry.get("coordinates") or []
            if len(coordinates) < 2:
                failed += 1
                continue

            lon = float(coordinates[0])
            lat = float(coordinates[1])
            ms = properties.get("time")
            if ms is None:
                failed += 1
                continue
            event_time = datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).replace(
                tzinfo=None
            )

            source_id = properties.get("net") or "USGS"
            title = properties.get("title") or properties.get("place") or "Untitled earthquake"

            existing = find_existing_event(
                db,
                title=title,
                event_time=event_time,
                source=source_id,
            )
            if existing:
                skipped += 1
                continue

            create_disaster_event(
                db,
                DisasterEventCreate(
                    title=title,
                    type="earthquake",
                    latitude=lat,
                    longitude=lon,
                    severity=_severity_from_earthquake_mag(properties.get("mag")),
                    source=source_id,
                    external_id=item.get("id"),
                    event_time=event_time,
                ),
                source_provider="USGS FDSN Event API",
            )
            inserted += 1
        except Exception:
            failed += 1

    complete_ingest_run(
        db,
        run,
        status="completed",
        requested_count=len(features),
        inserted_count=inserted,
        skipped_count=skipped,
        failed_count=failed,
    )

    return {
        "provider": "USGS FDSN Event API",
        "event_type": "earthquake",
        "requested": len(features),
        "inserted": inserted,
        "skipped_existing": skipped,
        "failed": failed,
        "filters": params,
    }


@router.get("/sources", response_model=list[SourceMetadataRead])
def list_registered_sources(db: Session = Depends(get_db)):
    return list_sources(db)


@router.get("/ingest/runs", response_model=list[IngestRunRead])
def list_ingestion_runs(
    provider: str | None = Query(default=None),
    dataset: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return list_ingest_runs(db, provider=provider, dataset=dataset, limit=limit)
