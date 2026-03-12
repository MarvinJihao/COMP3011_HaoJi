from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SourceMetadataRead(BaseModel):
    id: int
    source_key: str
    title: str
    provider: str
    source_url: Optional[str] = None
    description: Optional[str] = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
