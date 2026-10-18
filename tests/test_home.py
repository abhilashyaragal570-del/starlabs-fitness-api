def test_home_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "StarLabs Fitness Studio" in r.text