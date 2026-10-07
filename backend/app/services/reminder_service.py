from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.booking import Booking
from app.models.notification import Notification
from app.core.config import settings

def process_upcoming_event_reminders(db: Session) -> int:
    """
    Scans for events occurring within the reminder window (e.g. next 48 hours),
    finds users with active CONFIRMED bookings, and issues reminder notifications.
    Guarantees no duplicate reminders are sent for the same event and user.
    Returns the count of new reminder notifications created.
    """
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=settings.EVENT_REMINDER_HOURS_AHEAD)

    # Find events coming up in the window
    events = db.query(Event).filter(
        Event.event_date >= now,
        Event.event_date <= window_end
    ).all()

    reminders_created = 0

    for event in events:
        # Find all confirmed bookings for this event
        confirmed_bookings = db.query(Booking).filter(
            Booking.event_id == event.id,
            Booking.booking_status == "CONFIRMED"
        ).all()

        # Unique user IDs for this event
        user_ids = {b.user_id for b in confirmed_bookings}

        for user_id in user_ids:
            # Check if this user already received an EVENT reminder for this event
            expected_title = f"Upcoming Event Reminder: {event.title}"
            existing = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.type == "EVENT",
                Notification.title == expected_title
            ).first()

            if not existing:
                event_date_str = event.event_date.strftime("%A, %b %d at %I:%M %p")
                notification = Notification(
                    user_id=user_id,
                    title=expected_title,
                    message=f"Reminder! '{event.title}' is happening on {event_date_str} at {event.location}. Have your QR ticket ready!",
                    type="EVENT",
                    is_read=False
                )
                db.add(notification)
                reminders_created += 1

    if reminders_created > 0:
        db.commit()

    return reminders_created
