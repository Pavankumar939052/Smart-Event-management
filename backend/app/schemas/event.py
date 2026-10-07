from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Literal, List

VALID_CATEGORIES = ("Music", "Tech", "Sports", "Business")

class EventBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Event title")
    description: str = Field(..., min_length=10, description="Detailed description of the event")
    category: Literal["Music", "Tech", "Sports", "Business"] = Field(..., description="Event category")
    location: str = Field(..., min_length=2, max_length=255, description="Venue or city")
    event_date: datetime = Field(..., description="Date and time when the event takes place")
    ticket_price: float = Field(..., ge=0.0, description="Ticket price, non-negative")
    total_tickets: int = Field(default=100, gt=0, description="Total seating capacity")
    banner_image: str = Field(..., min_length=5, description="Image URL or path")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of {VALID_CATEGORIES}")
        return v

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    available_tickets: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventListResponse(BaseModel):
    total: int
    items: List[EventResponse]
