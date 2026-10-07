from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.models.ticket import Ticket
from app.models.notification import Notification
from app.core.security import hash_password
from app.services.ticket_service import generate_unique_ticket_code, generate_qr_code_data_uri

SAMPLE_EVENTS = [
    {
        "title": "Global AI & Cloud Summit 2026",
        "description": "Join 5,000+ engineers, researchers, and tech pioneers exploring Generative AI, distributed cloud architectures, quantum computing, and edge intelligence. Features keynotes from industry leaders, hands-on workshops, and deep tech exhibition.",
        "category": "Tech",
        "location": "Moscone Center, San Francisco, CA",
        "event_date": datetime.now(timezone.utc) + timedelta(days=1, hours=4), # Within 48 hours for reminder testing!
        "ticket_price": 149.99,
        "total_tickets": 300,
        "available_tickets": 298,
        "banner_image": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "Neon Horizon Electronic Music Festival",
        "description": "An electric 3-day outdoor music festival featuring world-renowned DJs, immersive LED light domes, live synth performances, and state-of-the-art spatial sound stages under the starlit desert sky.",
        "category": "Music",
        "location": "Downtown Arena & Arts District, Austin, TX",
        "event_date": datetime.now(timezone.utc) + timedelta(days=12),
        "ticket_price": 89.00,
        "total_tickets": 500,
        "available_tickets": 500,
        "banner_image": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "International Champions Football Classic",
        "description": "Witness world-class football live! Two legendary European clubs clash in a thrilling pre-season showdown with premier talent, high-intensity play, and an electrifying stadium atmosphere.",
        "category": "Sports",
        "location": "MetLife Stadium, East Rutherford, NJ",
        "event_date": datetime.now(timezone.utc) + timedelta(days=20),
        "ticket_price": 75.50,
        "total_tickets": 400,
        "available_tickets": 400,
        "banner_image": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "Future of Venture Capital & Fintech 2026",
        "description": "Exclusive gathering of angel investors, top venture partners, and high-growth fintech founders. Masterclasses in alternative assets, decentralized finance compliance, and AI dealflow automation.",
        "category": "Business",
        "location": "Hudson Yards Financial Center, New York, NY",
        "event_date": datetime.now(timezone.utc) + timedelta(days=30),
        "ticket_price": 299.00,
        "total_tickets": 150,
        "available_tickets": 150,
        "banner_image": "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "Symphony Under The Stars: Classical Odyssey",
        "description": "Experience Beethoven, Tchaikovsky, and modern cinematic orchestrations performed live by the Metropolitan Philharmonic Orchestra in an acoustic open-air amphitheater.",
        "category": "Music",
        "location": "Hollywood Bowl, Los Angeles, CA",
        "event_date": datetime.now(timezone.utc) + timedelta(days=15),
        "ticket_price": 60.00,
        "total_tickets": 250,
        "available_tickets": 250,
        "banner_image": "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "NextGen Web3 & Cyber Defense Summit",
        "description": "Deep-dive technical conference on zero-knowledge cryptography, secure enclave computing, and next-generation threat intelligence for modern enterprise engineering teams.",
        "category": "Tech",
        "location": "Seattle Convention Center, Seattle, WA",
        "event_date": datetime.now(timezone.utc) + timedelta(days=25),
        "ticket_price": 120.00,
        "total_tickets": 200,
        "available_tickets": 200,
        "banner_image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "National Marathon & Athletics Expo",
        "description": "Join 20,000 runners and fitness enthusiasts for the annual metropolitan marathon, 10K sprint, and interactive sports science expo showcasing cutting-edge athletic gear.",
        "category": "Sports",
        "location": "Grant Park, Chicago, IL",
        "event_date": datetime.now(timezone.utc) + timedelta(days=35),
        "ticket_price": 45.00,
        "total_tickets": 600,
        "available_tickets": 600,
        "banner_image": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3?auto=format&fit=crop&w=1200&q=80"
    },
    {
        "title": "Global Leadership & Sustainability Forum",
        "description": "Thought leadership symposium bringing together Fortune 500 executives, circular economy innovators, and sustainability policymakers to architect sustainable corporate strategies.",
        "category": "Business",
        "location": "Hynes Convention Center, Boston, MA",
        "event_date": datetime.now(timezone.utc) + timedelta(days=45),
        "ticket_price": 220.00,
        "total_tickets": 180,
        "available_tickets": 180,
        "banner_image": "https://images.unsplash.com/photo-1515187029135-18ee286d815b?auto=format&fit=crop&w=1200&q=80"
    }
]

def seed_database(db: Session):
    """Populates database with default seed events and a demo user if empty."""
    # Check if events already exist
    existing_events_count = db.query(Event).count()
    if existing_events_count == 0:
        for event_dict in SAMPLE_EVENTS:
            event = Event(**event_dict)
            db.add(event)
        db.commit()

    # Check if demo user exists
    demo_user = db.query(User).filter(User.email == "alex@example.com").first()
    if not demo_user:
        demo_user = User(
            username="alex_morgan",
            email="alex@example.com",
            hashed_password=hash_password("Password123!")
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        # Seed an initial booking for demo user on event 1 so tickets and notifications exist
        first_event = db.query(Event).first()
        if first_event:
            booking = Booking(
                user_id=demo_user.id,
                event_id=first_event.id,
                ticket_quantity=2,
                total_price=round(first_event.ticket_price * 2, 2),
                booking_status="CONFIRMED"
            )
            db.add(booking)
            db.flush()

            ticket_code = generate_unique_ticket_code(db)
            qr_uri = generate_qr_code_data_uri(ticket_code, first_event.id, booking.id)
            ticket = Ticket(
                booking_id=booking.id,
                ticket_code=ticket_code,
                qr_code_url=qr_uri,
                is_used=False
            )
            db.add(ticket)

            notification = Notification(
                user_id=demo_user.id,
                title="Welcome to SmartEvent! 🎉",
                message="Welcome to SmartEvent! Your demo account is ready, and your ticket for the Global AI Summit is confirmed.",
                type="SYSTEM",
                is_read=False
            )
            db.add(notification)
            db.commit()
