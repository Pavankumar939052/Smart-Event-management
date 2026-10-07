from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.event import EventResponse
from app.schemas.ticket import TicketResponse

class BookingCreate(BaseModel):
    event_id: int = Field(..., gt=0, description="Target event ID")
    ticket_quantity: int = Field(..., gt=0, description="Number of tickets to book (must be greater than 0)")

class BookingResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    ticket_quantity: int
    total_price: float
    booking_status: str
    created_at: datetime
    event: Optional[EventResponse] = None
    tickets: List[TicketResponse] = []

    model_config = ConfigDict(from_attributes=True)
