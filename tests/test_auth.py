from datetime import timedelta

import jwt

from app.config import settings
from app.timeutils import now_utc
from tests.helpers import auth_headers


def test_signup_success_hides_password(client):
    r = client.post("/signup", json={"name": "A", "email": "a@example.com", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@example.com"
    assert "password" not in body and "hashed_password" not in body


def test_signup_duplicate_email_is_409(client):
    payload = {"name": "A", "email": "a@example.com", "password": "password123"}
    assert client.post("/signup", json=payload).status_code == 201
    assert client.post("/signup", json={**payload, "email": "A@Example.com"}).status_code == 409


def test_signup_missing_fields_is_422(client):
    assert client.post("/signup", json={"email": "a@example.com"}).status_code == 422


def test_signup_short_password_is_422(client):
    r = client.post("/signup", json={"name": "A", "email": "a@example.com", "password": "short"})
    assert r.status_code == 422


def test_login_wrong_password_is_401(client):
    client.post("/signup", json={"name": "A", "email": "a@example.com", "password": "password123"})
    r = client.post("/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_login_unknown_user_is_401(client):
    r = client.post("/login", json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


def test_login_returns_bearer_token(client):
    client.post("/signup", json={"name": "A", "email": "a@example.com", "password": "password123"})
    r = client.post("/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and r.json()["access_token"]


def test_protected_endpoints_reject_missing_and_bad_tokens(client):
    class_body = {"name": "X", "dateTime": "2030-01-01T10:00:00Z", "instructor": "Y", "availableSlots": 5}
    book_body = {"class_id": 1, "client_name": "A", "client_email": "a@example.com"}
    bad = {"Authorization": "Bearer not-a-real-token"}

    assert client.post("/classes", json=class_body).status_code == 401
    assert client.post("/book", json=book_body).status_code == 401
    assert client.get("/bookings").status_code == 401
    assert client.post("/classes", json=class_body, headers=bad).status_code == 401
    assert client.get("/bookings", headers=bad).status_code == 401


def test_expired_token_is_rejected(client):
    auth_headers(client)  # creates user id 1
    now = now_utc()
    expired = jwt.encode(
        {"sub": "1", "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    r = client.get("/bookings", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_signed_with_wrong_key_is_rejected(client):
    auth_headers(client)
    forged = jwt.encode({"sub": "1", "exp": now_utc() + timedelta(hours=1)}, "some-other-key-0123456789abcdef", algorithm="HS256")
    assert client.get("/bookings", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_valid_token_is_accepted(client):
    h = auth_headers(client)
    assert client.get("/bookings", headers=h).status_code == 200