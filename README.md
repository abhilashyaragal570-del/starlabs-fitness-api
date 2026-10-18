# StarLabs Fitness Studio Booking API

A simple booking API for a fictional fitness studio, built with **Python**, **FastAPI**, **SQLAlchemy** and **SQLite**. Users sign up, log in with JWT authentication, create and browse classes, book slots, and view their own bookings.

## Features

- Signup and login with bcrypt password hashing and JWT access tokens (60 minute expiry)
- Protected endpoints: create class, book class, view own bookings
- Public listing of upcoming classes, sorted by start time
- Overbooking prevention using an atomic conditional slot decrement
- Duplicate booking prevention (same client email in the same class)
- Class times stored in IST, with optional conversion to other timezones
- Validation errors for missing or invalid fields
- Automated tests (29 tests)
- Interactive Swagger docs at `/docs`

## Tech Stack

- Python 3.10+
- FastAPI, Uvicorn
- SQLAlchemy 2.x with SQLite
- PyJWT, bcrypt
- pytest, httpx

## Project Structure

```text
app/
  main.py          FastAPI app and router registration
  config.py        Settings loaded from .env
  database.py      Engine, session, SQLite foreign keys
  models.py        User, FitnessClass, Booking
  schemas.py       Request and response models
  security.py      Password hashing and JWT helpers
  deps.py          get_current_user dependency
  timeutils.py     IST helpers and the IST column type
  seed.py          Sample data
  routers/         auth.py, classes.py, bookings.py
tests/             pytest suite
```

## Setup

### 1. Clone and enter the project

```bash
git clone https://github.com/abhilashyaragal570-del/starlabs-fitness-api.git
cd starlabs-fitness-api
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and set a real secret key.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

macOS / Linux:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the printed value into `.env` as `SECRET_KEY`.

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Secret used to sign JWTs (required) | none |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./fitness.db` |

### 5. Load sample data (optional)

```bash
python -m app.seed
```

This creates a demo user and 5 upcoming classes (always in the future, at fixed IST times).

- Demo email: `demo@starlabs.example`
- Demo password: `DemoPass123`

## Run Locally

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The SQLite file `fitness.db` is created automatically on first start.

## Run Tests

```bash
pytest -v
```

Tests use a separate database file (`test_fitness.db`), so your real data is not touched. They cover authentication, token rejection, validation, IST conversion, upcoming-class filtering, booking, duplicate prevention, overbooking, booking privacy and a concurrent last-slot booking.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/signup` | No | Register a new user |
| POST | `/login` | No | Log in and receive a JWT |
| POST | `/classes` | Yes | Create a class |
| GET | `/classes` | No | List upcoming classes |
| POST | `/book` | Yes | Book a slot in a class |
| GET | `/bookings` | Yes | List the authenticated user's bookings |

## API Usage (cURL)

### Sign up

```bash
curl -X POST http://127.0.0.1:8000/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"password123"}'
```

### Log in

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}'
```

Response:

```json
{ "access_token": "<JWT>", "token_type": "bearer" }
```

Use the token in the next requests:

```bash
TOKEN="<paste access_token here>"
```

### Create a class (auth required)

```bash
curl -X POST http://127.0.0.1:8000/classes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Yoga Flow","dateTime":"2030-06-15T10:00:00Z","instructor":"John Doe","availableSlots":20}'
```

Response (time returned in IST):

```json
{
  "id": 6,
  "name": "Yoga Flow",
  "dateTime": "2030-06-15T15:30:00+05:30",
  "instructor": "John Doe",
  "availableSlots": 20
}
```

### List upcoming classes

```bash
curl http://127.0.0.1:8000/classes
```

Optional timezone conversion:

```bash
curl "http://127.0.0.1:8000/classes?tz=UTC"
curl "http://127.0.0.1:8000/classes?tz=America/New_York"
```

### Book a class (auth required)

```bash
curl -X POST http://127.0.0.1:8000/book \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"class_id":1,"client_name":"Alice","client_email":"alice@example.com"}'
```

### View my bookings (auth required)

```bash
curl http://127.0.0.1:8000/bookings -H "Authorization: Bearer $TOKEN"
```

## Error Responses

| Status | When |
|---|---|
| 400 | Class already started, or unknown `tz` value |
| 401 | Missing, invalid or expired token; wrong login credentials |
| 404 | Class not found |
| 409 | Email already registered; client already booked in this class; class fully booked |
| 422 | Missing or invalid fields |

## Design Decisions

### Authentication

Passwords are hashed with bcrypt (max 72 bytes). Login returns a JWT signed with `SECRET_KEY` that expires after 60 minutes. Wrong email and wrong password return the same error. Token refresh is not implemented.

### Timezone policy

- Class times are **stored in IST** (Asia/Kolkata) as naive IST wall-clock values.
- Input with an explicit offset (for example `Z` or `-04:00`) is converted to IST.
- Input with no offset is interpreted as IST.
- Responses are in IST (`+05:30`) by default. `GET /classes?tz=<IANA zone>` converts the output.

### Booking and overbooking

- The slot is deducted with a single conditional `UPDATE ... WHERE available_slots > 0`, so two simultaneous requests cannot both take the last slot.
- A unique constraint on `(class_id, client_email)` prevents the same client booking a class twice.
- The booking row and the slot deduction commit together in one transaction, and roll back together on failure.
- Database check constraints keep `available_slots` between 0 and the class capacity.
- Classes that have already started cannot be booked.
- `GET /bookings` returns bookings made by the authenticated user (the account holder), including the client name and email supplied at booking time.

## Limitations

- SQLite is used for development. Concurrency was tested with threads against SQLite, not against PostgreSQL.
- Any authenticated user can create classes (the assignment defines no admin role).
- No token refresh, rate limiting or booking cancellation.
- No database migrations: tables are created on startup with `create_all`.