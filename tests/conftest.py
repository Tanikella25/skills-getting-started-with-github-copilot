"""
Pytest configuration and fixtures for FastAPI tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient for making requests to the FastAPI app.
    
    The client is connected to the live app with its shared in-memory database,
    allowing tests to modify state and observe changes across test runs.
    """
    return TestClient(app)
