from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingResponse
from app.dependencies.auth import get_current_user
from app.services.booking_service import create_booking_transaction, cancel_booking_transaction

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Book tickets for an event")
def book_ticket(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = create_booking_transaction(
        db=db,
        user=current_user,
        event_id=booking_in.event_id,
        ticket_quantity=booking_in.ticket_quantity
    )
    return booking

@router.get("/me", response_model=List[BookingResponse], summary="Get current user's booking history")
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking)\
        .options(joinedload(Booking.event), joinedload(Booking.tickets))\
        .filter(Booking.user_id == current_user.id)\
        .order_by(Booking.created_at.desc())\
        .all()
    return bookings

@router.get("/{booking_id}", response_model=BookingResponse, summary="Get details of a specific booking")
def get_booking_detail(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking)\
        .options(joinedload(Booking.event), joinedload(Booking.tickets))\
        .filter(Booking.id == booking_id)\
        .first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this booking."
        )

    return booking

@router.post("/{booking_id}/cancel", response_model=BookingResponse, summary="Cancel an existing booking")
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_booking = cancel_booking_transaction(
        db=db,
        user=current_user,
        booking_id=booking_id
    )
    return updated_booking
