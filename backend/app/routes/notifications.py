from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.dependencies.auth import get_current_user
from app.services.reminder_service import process_upcoming_event_reminders

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse], summary="Get current user's notifications")
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the authenticated user's notifications, ordered by newest first."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifications

@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark a notification as read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a single notification as read, enforcing strict user ownership."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found."
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this notification."
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

@router.patch("/mark-all-read", summary="Mark all notifications as read for current user")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks all unread notifications for the current authenticated user as read."""
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .update({"is_read": True})
    )
    db.commit()
    return {"message": f"Marked {unread_count} notifications as read."}

@router.post("/trigger-reminders", summary="Trigger upcoming event reminder scanner")
def trigger_event_reminders(db: Session = Depends(get_db)):
    """
    Scans for upcoming events and sends reminder notifications to users with bookings.
    Can be called by cron or scheduler. Prevents duplicate reminders.
    """
    created_count = process_upcoming_event_reminders(db)
    return {
        "status": "success",
        "reminders_created": created_count,
        "message": f"Processed upcoming event reminders. Created {created_count} new reminders."
    }
