from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.base import Base


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False, index=True)
    dataset = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="started")
    requested_count = Column(Integer, nullable=False, default=0)
    inserted_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    filters_json = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
