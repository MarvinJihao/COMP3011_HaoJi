from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DisasterEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: int = Field(..., ge=1, le=5)
    source: str = Field(..., min_length=1, max_length=100)
    event_time: datetime


class DisasterEventCreate(DisasterEventBase):
    external_id: Optional[str] = Field(default=None, max_length=150)


class DisasterEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    severity: Optional[int] = Field(default=None, ge=1, le=5)
    source: Optional[str] = Field(default=None, min_length=1, max_length=100)
    event_time: Optional[datetime] = None
    external_id: Optional[str] = Field(default=None, max_length=150)


class DisasterEventRead(DisasterEventBase):
    id: int
    external_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
