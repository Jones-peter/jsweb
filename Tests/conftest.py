"""Pytest configuration and shared fixtures for jsweb tests."""

import sys
from pathlib import Path

import pytest

# Add the parent directory to the path so we can import jsweb
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app():
    """Create a basic jsweb application for testing."""
    from jsweb import App
    
    app = App(__name__)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    # This is a simple implementation - you may need to adjust based on your app
    return app


@pytest.fixture
def config():
    """Provide a test configuration."""
    class TestConfig:
        DEBUG = True
        TESTING = True
        SECRET_KEY = "test-secret-key"
        DATABASE_URL = "sqlite:///:memory:"
        
    return TestConfig()


@pytest.fixture
def sample_form_data():
    """Provide sample form data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "age": 30,
        "active": True
    }
