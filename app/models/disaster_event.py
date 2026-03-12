from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class DisasterEvent(Base):
    __tablename__ = "disaster_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey("source_metadata.id"), nullable=False, index=True)
    external_id = Column(String(150), nullable=True, index=True)
    event_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_metadata = relationship("SourceMetadata")

    @property
    def type(self) -> str:
        return self.event_type

    @property
    def source(self) -> str | None:
        if self.source_metadata is None:
            return None
        return self.source_metadata.source_key
