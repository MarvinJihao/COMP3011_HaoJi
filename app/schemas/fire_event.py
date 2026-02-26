from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FireEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: int = Field(..., ge=1, le=5)
    source: str = Field(..., min_length=1, max_length=100)
    event_time: datetime


class FireEventCreate(FireEventBase):
    pass


class FireEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    severity: Optional[int] = Field(default=None, ge=1, le=5)
    source: Optional[str] = Field(default=None, min_length=1, max_length=100)
    event_time: Optional[datetime] = None
    


class FireEventRead(FireEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
