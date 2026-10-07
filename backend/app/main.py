from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.seeds.seed_data import seed_database
from app.services.reminder_service import process_upcoming_event_reminders
from app.routes import auth, users, events, bookings, tickets, notifications
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables are created
    Base.metadata.create_all(bind=engine)
    
    # Seed default events & demo user if empty
    db = SessionLocal()
    try:
        seed_database(db)
        # Check reminders on startup
        process_upcoming_event_reminders(db)
    finally:
        db.close()
        
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Event Discovery & Ticket Booking Platform with JWT auth, digital QR ticketing, and notifications.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev & testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(tickets.router)
app.include_router(notifications.router)

@app.get("/", tags=["General"])
def root():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", tags=["General"])
def health():
    return {"status": "ok"}
