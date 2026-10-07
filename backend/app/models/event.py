from sqlalchemy import Column, Integer, String, Text, Float, DateTime, CheckConstraint, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    ticket_price = Column(Float, nullable=False, default=0.0)
    total_tickets = Column(Integer, nullable=False, default=100)
    available_tickets = Column(Integer, nullable=False, default=100)
    banner_image = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("ticket_price >= 0", name="check_positive_ticket_price"),
        CheckConstraint("total_tickets >= 0", name="check_positive_total_tickets"),
        CheckConstraint("available_tickets >= 0", name="check_positive_available_tickets"),
        CheckConstraint("category IN ('Music', 'Tech', 'Sports', 'Business')", name="check_valid_category"),
    )

    bookings = relationship("Booking", back_populates="event", cascade="all, delete-orphan")
