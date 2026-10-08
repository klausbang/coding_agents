import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set"),
]


def test_health_against_real_postgres(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["database"] == "ok"
