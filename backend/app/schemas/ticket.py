from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TicketResponse(BaseModel):
    id: int
    booking_id: int
    ticket_code: str
    qr_code_url: str
    is_used: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TicketDetailResponse(BaseModel):
    id: int
    booking_id: int
    ticket_code: str
    qr_code_url: str
    is_used: bool
    created_at: datetime
    event_id: int
    event_title: str
    event_date: datetime
    location: str
    banner_image: str
    ticket_quantity: int
    total_price: float
    booking_status: str

    model_config = ConfigDict(from_attributes=True)

class TicketVerificationResponse(BaseModel):
    is_valid: bool
    ticket_code: str
    event_title: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    booking_status: Optional[str] = None
    ticket_quantity: Optional[int] = None
    attendee_username: Optional[str] = None
    is_used: bool = False
    message: str
