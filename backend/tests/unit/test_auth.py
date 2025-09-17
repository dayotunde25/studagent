"""
Unit tests for authentication module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    get_current_user,
    get_current_active_user
)
from app.models.user import User


class TestPasswordHashing:
    """Test cases for password hashing functions."""

    def test_password_hash_creation(self):
        """Test creating password hash."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert "$" in hashed  # bcrypt format

    def test_password_verification(self):
        """Test password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_password_verification_wrong_password(self):
        """Test password verification with wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


class TestTokenCreation:
    """Test cases for JWT token creation."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "test@example.com", "role": "student"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        # Token should have 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        # Token should have 3 parts separated by dots
        assert len(token.split(".")) == 3


class TestUserAuthentication:
    """Test cases for user authentication."""

    @patch('app.core.auth.get_db')
    def test_authenticate_user_success(self, mock_get_db):
        """Test successful user authentication."""
        # Mock database session
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        # Mock user
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = get_password_hash("password123")
        mock_user.is_active = True

        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = authenticate_user(mock_session, "test@example.com", "password123")

        assert result is not None
        assert result.email == "test@example.com"

    @patch('app.core.auth.get_db')
    def test_authenticate_user_wrong_password(self, mock_get_db):
        """Test authentication with wrong password."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = get_password_hash("password123")
        mock_user.is_active = True

        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = authenticate_user(mock_session, "test@example.com", "wrongpassword")

        assert result is False

    @patch('app.core.auth.get_db')
    def test_authenticate_user_nonexistent(self, mock_get_db):
        """Test authentication with nonexistent user."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = authenticate_user(mock_session, "nonexistent@example.com", "password123")

        assert result is False

    @patch('app.core.auth.get_db')
    def test_authenticate_user_inactive(self, mock_get_db):
        """Test authentication with inactive user."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = get_password_hash("password123")
        mock_user.is_active = False

        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = authenticate_user(mock_session, "test@example.com", "password123")

        assert result is False


class TestDependencyInjection:
    """Test cases for FastAPI dependency injection."""

    @patch('app.core.auth.jwt.decode')
    @patch('app.core.auth.get_db')
    def test_get_current_user_success(self, mock_get_db, mock_jwt_decode):
        """Test getting current user successfully."""
        # Mock JWT decode
        mock_jwt_decode.return_value = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # Mock database session
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        # Mock user
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock request
        mock_request = Mock()
        mock_request.headers.get.return_value = "Bearer fake_token"

        result = get_current_user(mock_request, mock_session)

        assert result is not None
        assert result.email == "test@example.com"

    @patch('app.core.auth.get_current_user')
    def test_get_current_active_user_success(self, mock_get_current_user):
        """Test getting current active user successfully."""
        mock_user = Mock()
        mock_user.is_active = True
        mock_get_current_user.return_value = mock_user

        result = get_current_active_user(mock_user)

        assert result == mock_user

    @patch('app.core.auth.get_current_user')
    def test_get_current_active_user_inactive(self, mock_get_current_user):
        """Test getting current active user when user is inactive."""
        from fastapi import HTTPException

        mock_user = Mock()
        mock_user.is_active = False
        mock_get_current_user.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(mock_user)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)

    def test_token_expiry_handling(self):
        """Test token expiry handling."""
        # Create a token that expires in the past
        past_time = datetime.utcnow() - timedelta(hours=1)
        data = {"sub": "test@example.com", "exp": past_time}

        with patch('app.core.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = data

            with pytest.raises(Exception):  # Should raise JWT error
                # This would normally be handled by the JWT library
                pass