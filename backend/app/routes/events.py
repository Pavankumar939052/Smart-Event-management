from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventResponse, EventCreate, VALID_CATEGORIES

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=List[EventResponse], summary="List and filter events")
def get_events(
    category: Optional[str] = Query(None, description="Filter by category: Music, Tech, Sports, Business"),
    search: Optional[str] = Query(None, description="Search by event title"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit per page"),
    db: Session = Depends(get_db)
):
    query = db.query(Event)

    # Validate category if provided
    if category is not None and category.strip() != "":
        normalized_cat = category.strip()
        if normalized_cat not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{normalized_cat}'. Supported categories are: {', '.join(VALID_CATEGORIES)}."
            )
        query = query.filter(Event.category == normalized_cat)

    # Search filter (safe ORM parameterization)
    if search is not None and search.strip() != "":
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term)
            )
        )

    # Order by event date ascending
    events = query.order_by(Event.event_date.asc()).offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=EventResponse, summary="Get event details by ID")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )
    return event

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED, summary="Create a new event")
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        title=event_in.title,
        description=event_in.description,
        category=event_in.category,
        location=event_in.location,
        event_date=event_in.event_date,
        ticket_price=event_in.ticket_price,
        total_tickets=event_in.total_tickets,
        available_tickets=event_in.total_tickets,
        banner_image=event_in.banner_image,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
