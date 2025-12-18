
import pytest
from app import create_app, db

@pytest.fixture(scope="function")
def app():
    _app = create_app("testing")
    _app.config["AI_ENABLE_FALLBACK"] = True  # Ensure fallback is enabled
    with _app.app_context():
        yield _app

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture
def auth_headers():
    def _headers(token):
        return {"Authorization": f"Bearer {token}"}
    return _headers

@pytest.fixture
def register_and_login(client):
    def _action(username="u1", email="u1@test.com", password="pw123"):
        client.post(
            "/api/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        r = client.post("/api/auth/login", json={"email": email, "password": password})
        data = r.get_json()
        return data["access_token"], data["user"]["id"]
    return _action
