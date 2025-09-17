"""
Pytest configuration and fixtures for Studagent backend tests.
"""

import asyncio
import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Create test database URL
    test_database_url = f"sqlite:///{db_path}"

    # Create engine
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "display_name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "role": "student",
        "is_active": True
    }


@pytest.fixture(scope="function")
def test_admin_data():
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "display_name": "Admin User",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "is_active": True
    }


@pytest.fixture(scope="function")
def auth_headers(client, test_user_data):
    """Create authentication headers for testing."""
    # Register user
    client.post("/api/v1/auth/register", json=test_user_data)

    # Login to get token
    response = client.post("/api/v1/auth/login", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client, test_admin_data):
    """Create admin authentication headers for testing."""
    # Register admin
    client.post("/api/v1/auth/register", json=test_admin_data)

    # Login to get token
    response = client.post("/api/v1/auth/login", data={
        "username": test_admin_data["email"],
        "password": test_admin_data["password"]
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_document_data():
    """Sample document data for testing."""
    return {
        "filename": "test_document.pdf",
        "content_type": "application/pdf",
        "size": 1024000,  # 1MB
        "user_id": 1
    }


@pytest.fixture(scope="function")
def sample_flashcard_data():
    """Sample flashcard data for testing."""
    return {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "document_id": 1,
        "user_id": 1
    }


@pytest.fixture(scope="function")
def sample_deadline_data():
    """Sample deadline data for testing."""
    return {
        "title": "Submit Assignment",
        "description": "Submit the final project assignment",
        "due_date": "2024-12-31T23:59:59Z",
        "priority": "high",
        "user_id": 1
    }