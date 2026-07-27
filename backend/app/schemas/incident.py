from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IncidentCreate(BaseModel):
    confidence: float
    image_path: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    user_id: int
    confidence: float
    image_path: Optional[str]
    status: str
    notified: bool
    detected_at: datetime

    model_config = {
        "from_attributes": True
    }