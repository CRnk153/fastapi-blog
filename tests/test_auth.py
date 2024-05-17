import jwt
import pytest
from fastapi.testclient import TestClient
from config import settings
from apps import app
from apps.routes import secure_router, guest_router  # admin_router
# noinspection PyUnresolvedReferences
from apps.routes import admin, auth, posts, users
from random import randint

app.include_router(secure_router)
app.include_router(guest_router)

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="module")
def user():
    user = {"username": f"test{randint(0,999)}",
            "email": f"test{randint(0,999)}@example.org",
            "password": f"test{randint(0,999)}"}
    yield user

def test_read_main(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world!", "user": None}

def test_register(client, user):
    response = client.post('/auth/register', json=user)
    assert response.status_code == 200

def test_login(client, user):
    response = client.post('/auth/login', json=user)
    assert response.status_code == 200
    token = response.cookies.get("access_token")
    client.cookies = {"access_token": token}
    assert token is not None
    response2 = client.get('/')
    assert response2.status_code == 200
    assert response2.json() == {"message": "Hello world!", "user": user["username"]}
    decoded_token = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
    decoded_token['exp'] -= 960
    token2 = jwt.encode(decoded_token, settings.SECRET_KEY, settings.ALGORITHM)
    client.cookies = {"access_token": token2}
    response3 = client.get('/')
    assert response3.status_code == 401
