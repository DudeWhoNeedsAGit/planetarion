def test_events_stream_requires_token(client):
    res = client.get("/api/events/stream")
    assert res.status_code == 401

