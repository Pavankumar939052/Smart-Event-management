from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.booking import Booking
from app.models.event import Event
from app.models.ticket import Ticket
from app.models.notification import Notification
from app.models.user import User
from app.services.ticket_service import generate_unique_ticket_code, generate_qr_code_data_uri

def create_booking_transaction(db: Session, user: User, event_id: int, ticket_quantity: int) -> Booking:
    """
    Executes an atomic database transaction to book tickets safely,
    preventing overbooking, calculating price server-side,
    and generating digital ticket and confirmation notification.
    """
    if ticket_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket quantity must be at least 1."
        )

    try:
        # Fetch event with row-level locking where supported (or transaction isolation)
        event = db.query(Event).filter(Event.id == event_id).with_for_update().first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found."
            )

        # Check event date: cannot book past events
        # Normalize timezone comparison
        now = datetime.now(timezone.utc)
        event_time = event.event_date
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        
        if event_time < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book tickets for an event that has already passed."
            )

        # Check availability
        if event.available_tickets <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This event is completely sold out."
            )

        if ticket_quantity > event.available_tickets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requested {ticket_quantity} tickets, but only {event.available_tickets} remaining."
            )

        # Calculate total price server-side
        total_price = round(event.ticket_price * ticket_quantity, 2)

        # Deduct available capacity
        event.available_tickets -= ticket_quantity

        # Create booking record
        booking = Booking(
            user_id=user.id,
            event_id=event.id,
            ticket_quantity=ticket_quantity,
            total_price=total_price,
            booking_status="CONFIRMED"
        )
        db.add(booking)
        db.flush()  # Populates booking.id without closing transaction

        # Generate unique ticket code and QR code
        ticket_code = generate_unique_ticket_code(db)
        qr_code_url = generate_qr_code_data_uri(ticket_code, event.id, booking.id)

        ticket = Ticket(
            booking_id=booking.id,
            ticket_code=ticket_code,
            qr_code_url=qr_code_url,
            is_used=False
        )
        db.add(ticket)

        # Create booking confirmation notification
        formatted_date = event_time.strftime("%b %d, %Y at %I:%M %p")
        notification = Notification(
            user_id=user.id,
            title="Booking Confirmed! 🎉",
            message=f"You successfully booked {ticket_quantity} ticket(s) for '{event.title}'. Scheduled for {formatted_date}. Total: ${total_price:.2f}.",
            type="BOOKING",
            is_read=False
        )
        db.add(notification)

        db.commit()
        db.refresh(booking)
        return booking

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process booking transaction: {str(e)}"
        )

def cancel_booking_transaction(db: Session, user: User, booking_id: int) -> Booking:
    """
    Cancels a confirmed booking, restoring the ticket availability
    and creating a cancellation notification for the user.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found."
        )

    # Ownership check
    if booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to cancel this booking."
        )

    if booking.booking_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled."
        )

    event = db.query(Event).filter(Event.id == booking.event_id).with_for_update().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated event not found."
        )

    try:
        # Restore available capacity
        event.available_tickets += booking.ticket_quantity
        booking.booking_status = "CANCELLED"

        # Create cancellation notification
        notification = Notification(
            user_id=user.id,
            title="Booking Cancelled",
            message=f"Your booking #{booking.id} for '{event.title}' has been cancelled. {booking.ticket_quantity} ticket capacity was released.",
            type="BOOKING",
            is_read=False
        )
        db.add(notification)

        db.commit()
        db.refresh(booking)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel booking: {str(e)}"
        )
