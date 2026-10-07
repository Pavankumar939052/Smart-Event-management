# SmartEvent — Event Discovery & Ticket Booking Platform (Phase 1)

Production-grade, full-stack event discovery, transactional ticket booking, and cryptographic digital ticketing platform built with **FastAPI**, **SQLAlchemy ORM**, **JWT Authentication**, **bcrypt**, **React (Vite)**, and **Axios**.

---

## 🚀 Key Features & Modules

### 1. User Authentication & Authorization (`/auth`, `/users`)
- **Secure Registration (`POST /auth/register`)**: Pydantic input validation, unique email and username enforcement (409 Conflict), bcrypt password hashing.
- **JWT Login (`POST /auth/login`)**: Supports email or username login, bcrypt password verification, signed JWT token with expiry.
- **Protected Profile (`GET /users/me`)**: Validates token claims via HTTP Bearer dependency and prevents ID spoofing.
- **Client Auth Flow**: Axios interceptor automatically attaches the JWT header, handles 401s, and protects routes with `ProtectedRoute`.

### 2. Event Discovery System (`/events`)
- **Event Catalog (`GET /events`)**: Filter by category (`Music`, `Tech`, `Sports`, `Business`), case-insensitive title and keyword search, pagination.
- **Event Details (`GET /events/{id}`)**: Real-time capacity counter, pricing, venue details, and interactive booking widget.
- **Validation**: Enforced category whitelist and non-negative pricing at both Pydantic and database constraint levels.

### 3. Transactional Ticket Booking (`/bookings`)
- **Booking Creation (`POST /bookings`)**:
  - Atomic database transactions with row-level concurrency locking (`with_for_update()`) to prevent race conditions and overbooking.
  - Server-side total price calculation: `total_price = event.ticket_price * quantity`.
  - Atomic generation of digital tickets, QR codes, and in-app confirmation notifications.
- **Booking History (`GET /bookings/me`)**: Strict user ownership filtering; users can only inspect their own bookings.
- **Booking Cancellation (`POST /bookings/{id}/cancel`)**: Allows users to cancel confirmed reservations, automatically restoring ticket capacity.

### 4. Digital QR Code Ticketing (`/tickets`)
- **Cryptographic Passes (`GET /tickets/me`)**: Collison-free unique ticket codes (`TKT-<UUID>`) with Base64 PNG Data URI QR codes.
- **Downloadable Passes**: Attendees can download or save QR codes directly as PNG files.
- **Verification API (`GET /tickets/verify/{ticket_code}`)**: Public/staff gate scanner validating authenticity and cancellation status without exposing sensitive user data.
- **Single-Use Check-In (`POST /tickets/check-in/{ticket_code}`)**: Enforces single-entry admission and prevents re-entry.

### 5. Notifications & Intelligent Event Reminders (`/notifications`)
- **Booking Confirmations**: Automatic instant notification on confirmed bookings.
- **Event Reminder Engine (`POST /notifications/trigger-reminders`)**:
  - Scans for upcoming events within the reminder window (e.g., next 48 hours).
  - Sends reminders only to users with valid confirmed tickets.
  - Guarantees duplicate prevention so users are not spammed.
- **Interactive UI**: Real-time unread bell badge, quick-view dropdown, mark as read, and full notification center.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.14 / FastAPI, Uvicorn |
| **Database** | SQL Database via SQLAlchemy ORM (SQLite / PostgreSQL ready) |
| **Auth & Security** | PyJWT (HS256), bcrypt password hashing |
| **Validation** | Pydantic v2 + email-validator |
| **Ticketing & QR** | Python `qrcode` + Pillow (Base64 PNG Data URIs) |
| **Frontend** | React 18, Vite 5, Tailwind CSS |
| **Icons & Design** | Lucide React |
| **HTTP Client** | Axios (with centralized interceptors) |
| **Testing** | Pytest, TestClient, HTTPX |

---

## 📂 Project Structure

```
Smart_event/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py         # Settings & environment variables
│   │   │   ├── database.py       # SQLAlchemy engine & session factory
│   │   │   └── security.py       # bcrypt hashing & JWT utilities
│   │   ├── dependencies/
│   │   │   └── auth.py           # get_current_user JWT dependency
│   │   ├── models/
│   │   │   ├── user.py           # User model & relationships
│   │   │   ├── event.py          # Event model & check constraints
│   │   │   ├── booking.py        # Booking model & status enum
│   │   │   ├── ticket.py         # Ticket model & unique codes
│   │   │   └── notification.py   # Notification model
│   │   ├── routes/
│   │   │   ├── auth.py           # /auth/register, /auth/login
│   │   │   ├── users.py          # /users/me
│   │   │   ├── events.py         # /events, /events/{id}
│   │   │   ├── bookings.py       # /bookings, /bookings/me, /bookings/{id}/cancel
│   │   │   ├── tickets.py        # /tickets/me, /tickets/verify/{code}, check-in
│   │   │   └── notifications.py  # /notifications, /notifications/{id}/read
│   │   ├── schemas/              # Pydantic v2 schemas
│   │   ├── seeds/
│   │   │   └── seed_data.py      # Seed realistic events & demo user
│   │   ├── services/
│   │   │   ├── booking_service.py # Transactional booking & cancellation
│   │   │   ├── ticket_service.py  # QR generation & verification logic
│   │   │   └── reminder_service.py# Duplicate-safe event reminder engine
│   │   └── main.py               # FastAPI entrypoint & CORS middleware
│   ├── tests/
│   │   └── test_backend.py       # Pytest automated test suite (16 tests)
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js          # Centralized Axios instance with interceptors
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Global auth state & token persistence
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Responsive navigation & user profile
│   │   │   ├── EventCard.jsx     # Event card with category & seats badge
│   │   │   ├── TicketCard.jsx    # QR digital pass with PNG download
│   │   │   ├── NotificationDropdown.jsx # Real-time notification drawer
│   │   │   └── ProtectedRoute.jsx# Auth route guard
│   │   ├── pages/
│   │   │   ├── HomePage.jsx      # Event discovery, search & filtering
│   │   │   ├── EventDetailPage.jsx # Details & live booking widget
│   │   │   ├── LoginPage.jsx     # Login with demo autofill
│   │   │   ├── RegisterPage.jsx  # Registration form with validation
│   │   │   ├── BookingConfirmationPage.jsx # Confirmation & digital pass
│   │   │   ├── BookingHistoryPage.jsx # Reservation history & cancellation
│   │   │   ├── TicketsPage.jsx   # Digital wallet for QR tickets
│   │   │   ├── NotificationsPage.jsx # Notifications center & reminder scanner
│   │   │   └── VerifyTicketPage.jsx  # Staff scanner & check-in tool
│   │   ├── App.jsx               # Route mappings
│   │   ├── main.jsx              # React mounting
│   │   └── index.css             # Tailwind base & custom design
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── .env
├── test_live_e2e.py              # End-to-end integration test runner
└── README.md
```

---

## ⚡ Quick Start

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment and activate
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and launch server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
- Open Frontend Web App: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Pre-Configured Demo Credentials

The platform seeds sample events and a demo account upon first launch:
- **Email**: `alex@example.com`
- **Password**: `Password123!`
- *(A convenient "Autofill" button is built directly into the Login page for 1-click login!)*

---

## 🧪 Testing & Verification

### Run Automated Backend Unit & Integration Tests:
```bash
cd backend
pytest -v
```
*(All 16 test cases covering auth, events, transactional bookings, overbooking race prevention, ownership checks, QR codes, notifications, and reminders pass).*

### Run Live End-to-End Test Suite:
```bash
python3 test_live_e2e.py
```
*(Executes live HTTP API calls against the running server validating the complete workflow).*
