from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.models.event import Event
from app.models.ticket import Ticket
from app.schemas.ticket import TicketDetailResponse, TicketVerificationResponse
from app.dependencies.auth import get_current_user
from app.services.ticket_service import verify_ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("/me", response_model=List[TicketDetailResponse], summary="Get all tickets for the authenticated user")
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches all digital tickets issued to the authenticated user,
    including linked event dates, locations, banner, and QR codes.
    """
    results = (
        db.query(Ticket, Booking, Event)
        .join(Booking, Ticket.booking_id == Booking.id)
        .join(Event, Booking.event_id == Event.id)
        .filter(Booking.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    tickets_data = []
    for ticket, booking, event in results:
        tickets_data.append(
            TicketDetailResponse(
                id=ticket.id,
                booking_id=ticket.booking_id,
                ticket_code=ticket.ticket_code,
                qr_code_url=ticket.qr_code_url,
                is_used=ticket.is_used,
                created_at=ticket.created_at,
                event_id=event.id,
                event_title=event.title,
                event_date=event.event_date,
                location=event.location,
                banner_image=event.banner_image,
                ticket_quantity=booking.ticket_quantity,
                total_price=booking.total_price,
                booking_status=booking.booking_status
            )
        )
    return tickets_data

@router.get("/verify/{ticket_code}", response_model=TicketVerificationResponse, summary="Verify ticket validity and booking authenticity")
def verify_ticket_code(
    ticket_code: str,
    db: Session = Depends(get_db)
):
    """
    Public/Staff verification endpoint to scan and validate a ticket QR code.
    Verifies ticket existence, booking status, and single-use check-in status.
    """
    verification_result = verify_ticket(db, ticket_code)
    return verification_result

@router.post("/check-in/{ticket_code}", response_model=TicketVerificationResponse, summary="Check-in and admit a ticket holder")
def check_in_ticket(
    ticket_code: str,
    db: Session = Depends(get_db)
):
    """
    Admits a ticket holder and marks ticket as used, preventing repeated entries.
    """
    verification = verify_ticket(db, ticket_code)
    if not verification["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=verification["message"]
        )

    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code.strip()).first()
    ticket.is_used = True
    db.commit()

    verification["is_used"] = True
    verification["message"] = "Ticket verified and checked-in successfully! Welcome to the event."
    return verification
