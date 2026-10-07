import os
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test DB is used
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-testing-32chars"

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.models.ticket import Ticket
from app.models.notification import Notification
from app.services.reminder_service import process_upcoming_event_reminders

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Helper to register and login
def create_test_user(username: str, email: str, password: str = "Password123!"):
    resp = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    return resp

def login_test_user(email_or_username: str, password: str = "Password123!"):
    resp = client.post("/auth/login", json={
        "email_or_username": email_or_username,
        "password": password
    })
    return resp

def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

# ======================== AUTHENTICATION TESTS ========================

def test_register_valid_user():
    resp = create_test_user("alice_dev", "alice@test.com")
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice_dev"
    assert data["email"] == "alice@test.com"
    assert "hashed_password" not in data

def test_register_duplicate_email():
    resp = create_test_user("alice_twin", "alice@test.com")
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]

def test_register_duplicate_username():
    resp = create_test_user("alice_dev", "other_alice@test.com")
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"]

def test_login_valid_credentials():
    resp = login_test_user("alice@test.com", "Password123!")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice_dev"

def test_login_with_username():
    resp = login_test_user("alice_dev", "Password123!")
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_invalid_password():
    resp = login_test_user("alice@test.com", "WrongPassword!")
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]

def test_access_protected_endpoint_without_jwt():
    resp = client.get("/users/me")
    assert resp.status_code == 401

def test_access_protected_endpoint_with_invalid_jwt():
    resp = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert resp.status_code == 401

def test_access_protected_endpoint_with_valid_jwt():
    login_resp = login_test_user("alice@test.com", "Password123!")
    token = login_resp.json()["access_token"]
    resp = client.get("/users/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice_dev"

# ======================== EVENTS TESTS ========================

def test_create_and_get_events():
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    # Create test event
    ev_resp = client.post("/events", json={
        "title": "Quantum Computing Expo 2026",
        "description": "Deep tech conference on superconducting qubits and algorithms.",
        "category": "Tech",
        "location": "Silicon Valley Convention Center",
        "event_date": future_date,
        "ticket_price": 50.0,
        "total_tickets": 20,
        "banner_image": "https://example.com/banner.jpg"
    })
    assert ev_resp.status_code == 201
    created_id = ev_resp.json()["id"]

    # Get event by ID
    get_resp = client.get(f"/events/{created_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Quantum Computing Expo 2026"

def test_get_nonexistent_event():
    resp = client.get("/events/999999")
    assert resp.status_code == 404

def test_filter_events_by_category():
    # Valid filter
    resp = client.get("/events?category=Tech")
    assert resp.status_code == 200
    items = resp.json()
    assert all(e["category"] == "Tech" for e in items)

    # Invalid category
    bad_cat_resp = client.get("/events?category=UnsupportedCategory")
    assert bad_cat_resp.status_code == 400

def test_search_events():
    resp = client.get("/events?search=Quantum")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("Quantum" in e["title"] for e in results)

def test_search_events_no_results():
    resp = client.get("/events?search=NonExistentSearchQueryXYZ123")
    assert resp.status_code == 200
    assert resp.json() == []

# ======================== BOOKING & TICKETS TESTS ========================

def test_booking_workflow_and_transaction():
    # 1. Create two users: bob (buyer) and charlie (other user)
    create_test_user("bob_buyer", "bob@test.com")
    bob_token = login_test_user("bob@test.com").json()["access_token"]
    create_test_user("charlie_viewer", "charlie@test.com")
    charlie_token = login_test_user("charlie@test.com").json()["access_token"]

    # Create a limited-capacity event (5 tickets)
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    ev_resp = client.post("/events", json={
        "title": "VIP Jazz Soiree",
        "description": "An intimate evening with world-renowned jazz saxophonists.",
        "category": "Music",
        "location": "Blue Note Lounge",
        "event_date": future_date,
        "ticket_price": 40.0,
        "total_tickets": 5,
        "banner_image": "https://example.com/jazz.jpg"
    })
    event_id = ev_resp.json()["id"]

    # Try booking without auth
    no_auth_resp = client.post("/bookings", json={"event_id": event_id, "ticket_quantity": 2})
    assert no_auth_resp.status_code == 401

    # Book valid quantity (2 tickets)
    book_resp = client.post("/bookings", json={"event_id": event_id, "ticket_quantity": 2}, headers=auth_headers(bob_token))
    assert book_resp.status_code == 201
    booking_data = book_resp.json()
    booking_id = booking_data["id"]
    assert booking_data["total_price"] == 80.0  # 40 * 2
    assert booking_data["booking_status"] == "CONFIRMED"
    assert len(booking_data["tickets"]) == 1
    ticket_code = booking_data["tickets"][0]["ticket_code"]
    assert ticket_code.startswith("TKT-")

    # Check available capacity decremented
    event_after = client.get(f"/events/{event_id}").json()
    assert event_after["available_tickets"] == 3

    # Attempt to book more tickets than available (e.g. 4 tickets when only 3 remain)
    overbook_resp = client.post("/bookings", json={"event_id": event_id, "ticket_quantity": 4}, headers=auth_headers(bob_token))
    assert overbook_resp.status_code == 409

    # Book remaining 3 tickets
    book_rem = client.post("/bookings", json={"event_id": event_id, "ticket_quantity": 3}, headers=auth_headers(bob_token))
    assert book_rem.status_code == 201

    # Now event is sold out (0 available)
    sold_out_resp = client.post("/bookings", json={"event_id": event_id, "ticket_quantity": 1}, headers=auth_headers(bob_token))
    assert sold_out_resp.status_code == 409
    assert "sold out" in sold_out_resp.json()["detail"].lower()

    # User Bob gets their bookings
    bob_bookings = client.get("/bookings/me", headers=auth_headers(bob_token)).json()
    assert len(bob_bookings) >= 2

    # User Charlie attempts to access Bob's booking
    charlie_access = client.get(f"/bookings/{booking_id}", headers=auth_headers(charlie_token))
    assert charlie_access.status_code == 403

    # Bob fetches their digital tickets
    bob_tickets = client.get("/tickets/me", headers=auth_headers(bob_token)).json()
    assert any(t["ticket_code"] == ticket_code for t in bob_tickets)

    # Charlie fetches their tickets -> should not see Bob's ticket
    charlie_tickets = client.get("/tickets/me", headers=auth_headers(charlie_token)).json()
    assert not any(t["ticket_code"] == ticket_code for t in charlie_tickets)

    # Verify ticket via public verify endpoint
    verify_resp = client.get(f"/tickets/verify/{ticket_code}")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["is_valid"] is True
    assert v_data["event_title"] == "VIP Jazz Soiree"
    assert v_data["attendee_username"] == "bob_buyer"

    # Check-in the ticket
    checkin_resp = client.post(f"/tickets/check-in/{ticket_code}")
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["is_used"] is True

    # Repeated check-in should be rejected
    checkin_repeat = client.post(f"/tickets/check-in/{ticket_code}")
    assert checkin_repeat.status_code == 400
    assert "already used" in checkin_repeat.json()["detail"].lower()

    # Cancellation test:
    # Cancel the second booking that booked 3 tickets
    rem_booking_id = book_rem.json()["id"]
    cancel_resp = client.post(f"/bookings/{rem_booking_id}/cancel", headers=auth_headers(bob_token))
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["booking_status"] == "CANCELLED"

    # Capacity should be restored by 3
    event_restored = client.get(f"/events/{event_id}").json()
    assert event_restored["available_tickets"] == 3

# ======================== NOTIFICATIONS & REMINDERS TESTS ========================

def test_notifications_workflow_and_ownership():
    # User Dave
    create_test_user("dave_notifications", "dave@test.com")
    dave_token = login_test_user("dave@test.com").json()["access_token"]
    create_test_user("eve_intruder", "eve@test.com")
    eve_token = login_test_user("eve@test.com").json()["access_token"]

    # Book an event to trigger a booking confirmation notification
    ev = client.post("/events", json={
        "title": "Upcoming Marathon Briefing",
        "description": "Mandatory briefing for marathon participants.",
        "category": "Sports",
        "location": "Memorial Stadium",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=1, hours=2)).isoformat(), # Within reminder window!
        "ticket_price": 10.0,
        "total_tickets": 50,
        "banner_image": "https://example.com/sports.jpg"
    }).json()

    # Dave books
    client.post("/bookings", json={"event_id": ev["id"], "ticket_quantity": 1}, headers=auth_headers(dave_token))

    # Fetch Dave's notifications
    dave_notifs = client.get("/notifications", headers=auth_headers(dave_token)).json()
    assert len(dave_notifs) >= 1
    booking_notif = dave_notifs[0]
    assert booking_notif["type"] == "BOOKING"
    assert booking_notif["is_read"] is False
    notif_id = booking_notif["id"]

    # Eve tries to mark Dave's notification as read -> 403 Forbidden
    intruder_patch = client.patch(f"/notifications/{notif_id}/read", headers=auth_headers(eve_token))
    assert intruder_patch.status_code == 403

    # Dave marks their notification as read
    patch_resp = client.patch(f"/notifications/{notif_id}/read", headers=auth_headers(dave_token))
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True

    # Test Event Reminder Engine
    db = TestingSessionLocal()
    try:
        new_reminders = process_upcoming_event_reminders(db)
        # Dave has confirmed booking on "Upcoming Marathon Briefing" which is in 26 hours, so reminder should be generated
        assert new_reminders >= 1

        # Test duplicate prevention: running again should create 0 reminders for this event & user
        no_duplicate = process_upcoming_event_reminders(db)
        assert no_duplicate == 0
    finally:
        db.close()
