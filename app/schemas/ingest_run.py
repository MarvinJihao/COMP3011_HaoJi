from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IngestRunRead(BaseModel):
    id: int
    provider: str
    dataset: str
    status: str
    requested_count: int
    inserted_count: int
    skipped_count: int
    failed_count: int
    filters_json: Optional[str] = None
    message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
