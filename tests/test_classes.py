from tests.helpers import auth_headers, future_iso, make_class, parse_dt, past_iso


def test_get_classes_is_public_and_empty_initially(client):
    r = client.get("/classes")
    assert r.status_code == 200 and r.json() == []


def test_create_class_response_shape(client):
    h = auth_headers(client)
    c = make_class(client, h, slots=20)
    assert set(c) == {"id", "name", "dateTime", "instructor", "availableSlots"}
    assert c["availableSlots"] == 20


def test_create_class_missing_or_invalid_fields_is_422(client):
    h = auth_headers(client)
    assert client.post("/classes", json={"name": "X"}, headers=h).status_code == 422
    bad = {"name": "X", "dateTime": future_iso(), "instructor": "Y", "availableSlots": 0}
    assert client.post("/classes", json=bad, headers=h).status_code == 422
    bad["availableSlots"] = 5
    bad["dateTime"] = "not-a-date"
    assert client.post("/classes", json=bad, headers=h).status_code == 422


def test_only_upcoming_classes_are_listed_and_sorted(client):
    h = auth_headers(client)
    make_class(client, h, name="Later", date_time=future_iso(days=5))
    make_class(client, h, name="Sooner", date_time=future_iso(days=1))
    make_class(client, h, name="Past", date_time=past_iso(days=3))
    names = [c["name"] for c in client.get("/classes").json()]
    assert names == ["Sooner", "Later"]


def test_utc_input_is_stored_and_returned_in_ist(client):
    h = auth_headers(client)
    r = client.post(
        "/classes",
        json={"name": "Y", "dateTime": "2030-06-15T10:00:00Z", "instructor": "J", "availableSlots": 5},
        headers=h,
    )
    assert r.json()["dateTime"] == "2030-06-15T15:30:00+05:30"
    assert client.get("/classes").json()[0]["dateTime"] == "2030-06-15T15:30:00+05:30"


def test_naive_input_is_interpreted_as_ist(client):
    h = auth_headers(client)
    r = client.post(
        "/classes",
        json={"name": "Y", "dateTime": "2030-06-15T10:00:00", "instructor": "J", "availableSlots": 5},
        headers=h,
    )
    assert r.json()["dateTime"] == "2030-06-15T10:00:00+05:30"


def test_explicit_offset_is_converted_to_ist(client):
    h = auth_headers(client)
    r = client.post(
        "/classes",
        json={"name": "Y", "dateTime": "2030-06-15T10:00:00-04:00", "instructor": "J", "availableSlots": 5},
        headers=h,
    )
    assert r.json()["dateTime"] == "2030-06-15T19:30:00+05:30"


def test_tz_query_converts_output_to_other_zone(client):
    h = auth_headers(client)
    make_class(client, h, date_time="2030-06-15T10:00:00Z")

    utc = parse_dt(client.get("/classes", params={"tz": "UTC"}).json()[0]["dateTime"])
    assert utc.utcoffset().total_seconds() == 0
    assert (utc.year, utc.month, utc.day, utc.hour, utc.minute) == (2030, 6, 15, 10, 0)

    ny = parse_dt(client.get("/classes", params={"tz": "America/New_York"}).json()[0]["dateTime"])
    assert ny.utcoffset().total_seconds() == -4 * 3600
    assert ny.hour == 6


def test_invalid_tz_is_400(client):
    assert client.get("/classes", params={"tz": "Not/AZone"}).status_code == 400