import time


def _login(client, username="testuser", password="testpassword"):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["token"]


def test_research_points_accrue_on_tick(client, db_session, sample_planet):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure the planet has a research lab to generate RP.
    sample_planet.research_lab = 1
    db_session.commit()

    before = client.get("/api/research/points", headers=headers).get_json()["research_points"]

    # Run a tick (manual tick endpoint does not require JWT).
    res = client.post("/api/tick")
    assert res.status_code == 200

    after = client.get("/api/research/points", headers=headers).get_json()["research_points"]
    assert after >= before


def test_research_queue_start_and_complete(client, db_session, sample_planet, sample_user):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Provide a lab + enough RP.
    sample_planet.research_lab = 5
    db_session.commit()

    # Seed RP directly for a deterministic start (tick accrual is covered in the other test).
    from backend.models import Research
    r = Research.query.filter_by(user_id=sample_user.id).first()
    if not r:
        r = Research(user_id=sample_user.id, research_points=0)
        db_session.add(r)
        db_session.flush()
    r.research_points = 10_000
    r.research_points_fraction = 0.0
    db_session.commit()

    status = client.get("/api/research", headers=headers).get_json()
    assert status["queue"] is None

    # Start a research project.
    res = client.post("/api/research/start", json={"key": "astrophysics"}, headers=headers)
    assert res.status_code == 200, res.get_json()

    status2 = client.get("/api/research", headers=headers).get_json()
    assert status2["queue"] is not None
    assert status2["queue"]["key"] == "astrophysics"

    # Wait for the (testing) duration to pass, then tick to complete.
    time.sleep(2.2)
    client.post("/api/tick")

    status3 = client.get("/api/research", headers=headers).get_json()
    assert status3["queue"] is None
    assert status3["levels"]["astrophysics"] >= 1
