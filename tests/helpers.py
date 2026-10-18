from datetime import datetime, timedelta, timezone


def future_iso(days: int = 2, hours: int = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days, hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def past_iso(days: int = 2) -> str:
    return future_iso(days=-days)


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def auth_headers(client, email="user@example.com", name="User", password="password123"):
    client.post("/signup", json={"name": name, "email": email, "password": password})
    r = client.post("/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_class(client, headers, slots=5, name="Yoga Flow", date_time=None):
    r = client.post(
        "/classes",
        json={
            "name": name,
            "dateTime": date_time or future_iso(),
            "instructor": "John Doe",
            "availableSlots": slots,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def book(client, headers, class_id, email="alice@example.com", name="Alice"):
    return client.post(
        "/book",
        json={"class_id": class_id, "client_name": name, "client_email": email},
        headers=headers,
    )