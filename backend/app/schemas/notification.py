from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Literal

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: Literal["EVENT", "BOOKING", "SYSTEM"]
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
