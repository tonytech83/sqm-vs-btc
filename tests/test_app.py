import pytest
from flask import Flask
from app import create_app

@pytest.fixture
def app() -> Flask:
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    return app

@pytest.fixture
def client(app: Flask):
    """A test client for the app."""
    return app.test_client()

def test_index(client):
    """Test the index page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"BTC Price" in response.data

def test_data(client):
    """Test the data endpoint."""
    response = client.get("/data")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_update_db(client):
    """Test the update-db endpoint."""
    response = client.get("/update-db")
    assert response.status_code == 200
    assert response.json["status"] == "Database updated" 