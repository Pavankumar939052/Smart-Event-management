from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    booking_status = Column(String(20), nullable=False, default="CONFIRMED", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("ticket_quantity > 0", name="check_positive_ticket_quantity"),
        CheckConstraint("total_price >= 0", name="check_positive_total_price"),
        CheckConstraint("booking_status IN ('PENDING', 'CONFIRMED', 'CANCELLED')", name="check_valid_booking_status"),
    )

    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
    tickets = relationship("Ticket", back_populates="booking", cascade="all, delete-orphan")
