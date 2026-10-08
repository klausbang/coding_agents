def test_health_reports_ok_when_database_reachable(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_index_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<h1>" in response.data
