import pytest

from app import create_app
from app.store import InventoryStore


@pytest.fixture
def app():
    """A fresh app with a fresh copy of the mock data for every test."""
    return create_app({"TESTING": True, "STORE": InventoryStore()})


@pytest.fixture
def client(app):
    return app.test_client()
