from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import DatabaseHealthRead, HealthRead

router = APIRouter()


@router.get("/health", response_model=HealthRead, status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "disaster-event-intelligence-api"}


@router.get("/health/db", response_model=DatabaseHealthRead, status_code=status.HTTP_200_OK)
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from exc

    return {"status": "ok", "database": "connected"}
