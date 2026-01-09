"""Pytest configuration and shared fixtures for jsweb tests."""

import sys
from io import BytesIO
from pathlib import Path

import pytest

# Add the parent directory to the path so we can import jsweb
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app():
    """Create a basic jsweb application for testing."""
    from jsweb import App

    app = App(__name__)
    app.config.TESTING = True
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
        SQLALCHEMY_ECHO = False

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
    return {"name": "Test User", "email": "test@example.com", "age": 30, "active": True}


@pytest.fixture
def fake_environ():
    """Provide a fake WSGI environ dict for request testing."""

    def _make_environ(
        method="GET",
        path="/",
        query_string="",
        content_type="application/x-www-form-urlencoded",
        content_length=0,
        body=b"",
        cookies="",
    ):
        return {
            "REQUEST_METHOD": method,
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "HTTP_COOKIE": cookies,
            "wsgi.input": BytesIO(body),
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
        }

    return _make_environ


@pytest.fixture
def json_request_environ(fake_environ):
    """Create a JSON POST request environ."""
    import json

    data = {"key": "value", "number": 42}
    body = json.dumps(data).encode("utf-8")

    return fake_environ(
        method="POST",
        path="/api/test",
        content_type="application/json",
        content_length=len(body),
        body=body,
    )


@pytest.fixture
def form_request_environ(fake_environ):
    """Create a form POST request environ."""
    body = b"username=testuser&email=test@example.com"

    return fake_environ(
        method="POST",
        path="/form",
        content_type="application/x-www-form-urlencoded",
        content_length=len(body),
        body=body,
    )


@pytest.fixture
def file_upload_environ(fake_environ):
    """Create a file upload request environ."""
    boundary = "----WebKitFormBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        f"Content-Type: text/plain\r\n"
        f"\r\n"
        f"test file content\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    return fake_environ(
        method="POST",
        path="/upload",
        content_type=f"multipart/form-data; boundary={boundary}",
        content_length=len(body),
        body=body,
    )


# Markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test individual components"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that test multiple components together",
    )
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "asyncio: Async tests")
    config.addinivalue_line("markers", "forms: Form validation tests")
    config.addinivalue_line("markers", "routing: Routing tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "security: Security tests")
