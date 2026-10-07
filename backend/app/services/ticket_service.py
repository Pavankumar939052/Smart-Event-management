import io
import json
import uuid
import base64
import qrcode
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.booking import Booking
from app.models.event import Event
from app.models.user import User

def generate_unique_ticket_code(db: Session, prefix: str = "TKT") -> str:
    """Generates a cryptographically random, collision-free ticket code."""
    while True:
        code_suffix = uuid.uuid4().hex[:12].upper()
        ticket_code = f"{prefix}-{code_suffix}"
        # Ensure code doesn't exist in DB
        existing = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
        if not existing:
            return ticket_code

def generate_qr_code_data_uri(ticket_code: str, event_id: int, booking_id: int) -> str:
    """Generates a QR code image encoded as a base64 Data URI."""
    payload = json.dumps({
        "ticket_code": ticket_code,
        "event_id": event_id,
        "booking_id": booking_id,
        "type": "SMART_EVENT_TICKET"
    })
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def verify_ticket(db: Session, ticket_code: str) -> dict:
    """Verifies a ticket by code and returns structured verification details."""
    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code.strip()).first()
    if not ticket:
        return {
            "is_valid": False,
            "ticket_code": ticket_code,
            "message": "Ticket not found. This ticket code does not exist in our system."
        }
    
    booking = db.query(Booking).filter(Booking.id == ticket.booking_id).first()
    if not booking:
        return {
            "is_valid": False,
            "ticket_code": ticket_code,
            "message": "Associated booking not found."
        }
        
    event = db.query(Event).filter(Event.id == booking.event_id).first()
    user = db.query(User).filter(User.id == booking.user_id).first()
    
    if booking.booking_status == "CANCELLED":
        return {
            "is_valid": False,
            "ticket_code": ticket_code,
            "event_title": event.title if event else "Unknown",
            "event_date": event.event_date if event else None,
            "location": event.location if event else None,
            "booking_status": "CANCELLED",
            "ticket_quantity": booking.ticket_quantity,
            "attendee_username": user.username if user else "Unknown",
            "is_used": ticket.is_used,
            "message": "This ticket has been CANCELLED and is no longer valid for entry."
        }

    if ticket.is_used:
        return {
            "is_valid": False,
            "ticket_code": ticket_code,
            "event_title": event.title if event else "Unknown",
            "event_date": event.event_date if event else None,
            "location": event.location if event else None,
            "booking_status": booking.booking_status,
            "ticket_quantity": booking.ticket_quantity,
            "attendee_username": user.username if user else "Unknown",
            "is_used": True,
            "message": "Ticket is already USED. Cannot be accepted for admission again."
        }

    return {
        "is_valid": True,
        "ticket_code": ticket_code,
        "event_title": event.title if event else "Unknown",
        "event_date": event.event_date if event else None,
        "location": event.location if event else None,
        "booking_status": booking.booking_status,
        "ticket_quantity": booking.ticket_quantity,
        "attendee_username": user.username if user else "Unknown",
        "is_used": False,
        "message": "Valid ticket! Admitted."
    }
