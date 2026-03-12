from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db.base import Base


class SourceMetadata(Base):
    __tablename__ = "source_metadata"

    id = Column(Integer, primary_key=True, index=True)
    source_key = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
