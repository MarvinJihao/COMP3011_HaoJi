import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.ingest_run import IngestRun


def create_ingest_run(
    db: Session,
    *,
    provider: str,
    dataset: str,
    filters: Optional[dict[str, Any]] = None,
) -> IngestRun:
    run = IngestRun(
        provider=provider,
        dataset=dataset,
        status="started",
        filters_json=json.dumps(filters or {}, sort_keys=True),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def complete_ingest_run(
    db: Session,
    run: IngestRun,
    *,
    status: str,
    requested_count: int,
    inserted_count: int,
    skipped_count: int,
    failed_count: int,
    message: Optional[str] = None,
) -> IngestRun:
    run.status = status
    run.requested_count = requested_count
    run.inserted_count = inserted_count
    run.skipped_count = skipped_count
    run.failed_count = failed_count
    run.message = message
    run.finished_at = datetime.utcnow()
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_ingest_runs(
    db: Session,
    *,
    provider: Optional[str] = None,
    dataset: Optional[str] = None,
    limit: int = 50,
) -> list[IngestRun]:
    query = db.query(IngestRun)
    if provider:
        query = query.filter(IngestRun.provider == provider)
    if dataset:
        query = query.filter(IngestRun.dataset == dataset)
    return query.order_by(IngestRun.started_at.desc()).limit(limit).all()
