from concurrent.futures import ThreadPoolExecutor

from tests.helpers import auth_headers, book, future_iso, make_class, past_iso


def slots_left(client, class_id):
    return next(c["availableSlots"] for c in client.get("/classes").json() if c["id"] == class_id)


def test_booking_success_deducts_one_slot(client):
    h = auth_headers(client)
    c = make_class(client, h, slots=5)
    r = book(client, h, c["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["class_id"] == c["id"] and body["client_email"] == "alice@example.com"
    assert slots_left(client, c["id"]) == 4


def test_duplicate_booking_is_409_and_keeps_slots(client):
    h = auth_headers(client)
    c = make_class(client, h, slots=5)
    assert book(client, h, c["id"]).status_code == 201
    assert book(client, h, c["id"]).status_code == 409
    assert slots_left(client, c["id"]) == 4


def test_full_class_is_409_and_never_goes_negative(client):
    h = auth_headers(client)
    c = make_class(client, h, slots=2)
    assert book(client, h, c["id"], "a@example.com").status_code == 201
    assert book(client, h, c["id"], "b@example.com").status_code == 201
    r = book(client, h, c["id"], "c@example.com")
    assert r.status_code == 409 and "fully booked" in r.json()["detail"].lower()
    assert slots_left(client, c["id"]) == 0
    assert len(client.get("/bookings", headers=h).json()) == 2


def test_unknown_class_is_404(client):
    h = auth_headers(client)
    assert book(client, h, 9999).status_code == 404


def test_past_class_cannot_be_booked(client):
    h = auth_headers(client)
    c = make_class(client, h, date_time=past_iso(days=1))
    assert book(client, h, c["id"]).status_code == 400


def test_booking_missing_or_invalid_fields_is_422(client):
    h = auth_headers(client)
    assert client.post("/book", json={"class_id": 1}, headers=h).status_code == 422
    bad = {"class_id": 1, "client_name": "A", "client_email": "not-an-email"}
    assert client.post("/book", json=bad, headers=h).status_code == 422


def test_bookings_are_private_to_each_user(client):
    ha = auth_headers(client, email="a@example.com")
    hb = auth_headers(client, email="b@example.com")
    c = make_class(client, ha, slots=5)
    assert book(client, ha, c["id"], "x@example.com").status_code == 201
    assert book(client, hb, c["id"], "y@example.com").status_code == 201

    a_emails = [b["client_email"] for b in client.get("/bookings", headers=ha).json()]
    b_emails = [b["client_email"] for b in client.get("/bookings", headers=hb).json()]
    assert a_emails == ["x@example.com"]
    assert b_emails == ["y@example.com"]


def test_bookings_response_shape_and_ist(client):
    h = auth_headers(client)
    c = make_class(client, h, date_time="2030-06-15T10:00:00Z")
    book(client, h, c["id"])
    item = client.get("/bookings", headers=h).json()[0]
    assert item["class_name"] == "Yoga Flow"
    assert item["dateTime"] == "2030-06-15T15:30:00+05:30"
    assert item["booked_at"].endswith("+05:30")


def test_concurrent_booking_of_last_slot_allows_only_one(client):
    h = auth_headers(client)
    c = make_class(client, h, slots=1)

    def attempt(i):
        return book(client, h, c["id"], email=f"user{i}@example.com", name=f"User {i}").status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(attempt, range(8)))

    assert codes.count(201) == 1, codes
    assert codes.count(409) == 7, codes
    assert slots_left(client, c["id"]) == 0
    assert len(client.get("/bookings", headers=h).json()) == 1