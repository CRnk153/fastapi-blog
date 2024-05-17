import pytest
from fastapi.testclient import TestClient
from apps import app

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def test_read_main(client):
    response = client.get('/')
    assert response.status_code == 200
