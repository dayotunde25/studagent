"""
Integration tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """Test cases for authentication API endpoints."""

    def test_register_user_success(self, client: TestClient, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_register_user_duplicate_email(self, client: TestClient, test_user_data):
        """Test registration with duplicate email."""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register with same email
        duplicate_data = test_user_data.copy()
        duplicate_data["display_name"] = "Different User"

        response = client.post("/api/v1/auth/register", json=duplicate_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower() or "unique" in data["detail"].lower()

    def test_register_user_invalid_data(self, client: TestClient):
        """Test registration with invalid data."""
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "123",  # Too short
            "display_name": ""
        }

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_login_success(self, client: TestClient, test_user_data):
        """Test successful login."""
        # First register the user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Then login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    def test_login_wrong_password(self, client: TestClient, test_user_data):
        """Test login with wrong password."""
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_refresh_token_success(self, client: TestClient, test_user_data):
        """Test successful token refresh."""
        # Register and login to get tokens
        client.post("/api/v1/auth/register", json=test_user_data)

        login_response = client.post("/api/v1/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })

        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    def test_get_current_user_authenticated(self, client: TestClient, auth_headers):
        """Test getting current user when authenticated."""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "display_name" in data
        assert "role" in data

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user when not authenticated."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_update_user_profile(self, client: TestClient, auth_headers):
        """Test updating user profile."""
        update_data = {
            "display_name": "Updated Name",
            "bio": "Updated bio",
            "interests": ["AI", "Machine Learning"]
        }

        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert "AI" in data["interests"]

    def test_update_user_profile_invalid_data(self, client: TestClient, auth_headers):
        """Test updating user profile with invalid data."""
        update_data = {
            "email": "invalid-email",  # Invalid email
            "display_name": ""  # Empty display name
        }

        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_get_user_by_id(self, client: TestClient, auth_headers, test_user_data):
        """Test getting user by ID."""
        # First get current user to get ID
        me_response = client.get("/api/v1/users/me", headers=auth_headers)
        user_id = me_response.json()["id"]

        # Then get user by ID
        response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == test_user_data["email"]

    def test_get_user_by_id_not_found(self, client: TestClient, auth_headers):
        """Test getting user by ID when user doesn't exist."""
        response = client.get("/api/v1/users/99999", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_password_reset_request(self, client: TestClient, test_user_data):
        """Test password reset request."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)

        reset_data = {
            "email": test_user_data["email"]
        }

        response = client.post("/api/v1/auth/forgot-password", json=reset_data)

        # This might return 200 even if email doesn't exist for security
        assert response.status_code in [200, 404]

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"