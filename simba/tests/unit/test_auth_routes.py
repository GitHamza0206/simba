import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from simba.__main__ import create_app
from simba.api.auth_routes import auth_router
from simba.auth.auth_service import AuthService


@pytest.fixture
def client():
    """Create a FastAPI TestClient for the app."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Mock the AuthService class methods."""
    with patch.object(AuthService, 'sign_up', new_callable=AsyncMock) as mock_sign_up, \
         patch.object(AuthService, 'sign_in', new_callable=AsyncMock) as mock_sign_in, \
         patch.object(AuthService, 'sign_out', new_callable=AsyncMock) as mock_sign_out, \
         patch.object(AuthService, 'reset_password', new_callable=AsyncMock) as mock_reset_password, \
         patch.object(AuthService, 'refresh_token', new_callable=AsyncMock) as mock_refresh_token:
        
        yield {
            'sign_up': mock_sign_up,
            'sign_in': mock_sign_in,
            'sign_out': mock_sign_out,
            'reset_password': mock_reset_password,
            'refresh_token': mock_refresh_token
        }


class TestAuthRoutes:
    """Tests for the authentication API routes."""
    
    def test_signup_success(self, client, mock_auth_service):
        """Test successful user signup."""
        # Mock the sign_up service response
        mock_auth_service['sign_up'].return_value = {
            "id": "test-user-id",
            "email": "new@example.com",
            "created_at": "2023-01-01T00:00:00",
            "metadata": {"role": "user"}
        }
        
        # Send a request to the signup endpoint
        response = client.post(
            "/auth/signup",
            json={
                "email": "new@example.com",
                "password": "securePassword123",
                "metadata": {"role": "user"}
            }
        )
        
        # Verify the response
        assert response.status_code == 201
        assert response.json()["id"] == "test-user-id"
        assert response.json()["email"] == "new@example.com"
        
        # Verify the service was called with correct parameters
        mock_auth_service['sign_up'].assert_called_once_with(
            email="new@example.com",
            password="securePassword123",
            user_metadata={"role": "user"}
        )
    
    def test_signup_error(self, client, mock_auth_service):
        """Test signup failure (email already exists)."""
        # Mock the sign_up service to raise an error
        mock_auth_service['sign_up'].side_effect = ValueError("Failed to sign up: Email already registered")
        
        # Send a request to the signup endpoint
        response = client.post(
            "/auth/signup",
            json={
                "email": "existing@example.com",
                "password": "securePassword123"
            }
        )
        
        # Verify the response
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
        
        # Verify the service was called
        mock_auth_service['sign_up'].assert_called_once()
    
    def test_signin_success(self, client, mock_auth_service):
        """Test successful user signin."""
        # Mock the sign_in service response
        mock_auth_service['sign_in'].return_value = {
            "user": {
                "id": "test-user-id",
                "email": "user@example.com",
                "metadata": {"role": "user"}
            },
            "session": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 1672531200
            }
        }
        
        # Send a request to the signin endpoint
        response = client.post(
            "/auth/signin",
            json={
                "email": "user@example.com",
                "password": "correctPassword123"
            }
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["user"]["id"] == "test-user-id"
        assert response.json()["session"]["access_token"] == "test-access-token"
        
        # Verify the service was called with correct parameters
        mock_auth_service['sign_in'].assert_called_once_with(
            email="user@example.com",
            password="correctPassword123"
        )
    
    def test_signin_error(self, client, mock_auth_service):
        """Test signin failure (invalid credentials)."""
        # Mock the sign_in service to raise an error
        mock_auth_service['sign_in'].side_effect = ValueError("Failed to sign in: Invalid credentials")
        
        # Send a request to the signin endpoint
        response = client.post(
            "/auth/signin",
            json={
                "email": "user@example.com",
                "password": "wrongPassword"
            }
        )
        
        # Verify the response
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
        
        # Verify the service was called
        mock_auth_service['sign_in'].assert_called_once()
    
    def test_signout_success(self, client, mock_auth_service):
        """Test successful user signout."""
        # Mock the sign_out service response
        mock_auth_service['sign_out'].return_value = None
        
        # Send a request to the signout endpoint
        response = client.post("/auth/signout")
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully signed out"
        
        # Verify the service was called
        mock_auth_service['sign_out'].assert_called_once()
    
    def test_reset_password_success(self, client, mock_auth_service):
        """Test successful password reset request."""
        # Mock the reset_password service response
        mock_auth_service['reset_password'].return_value = None
        
        # Send a request to the reset-password endpoint
        response = client.post(
            "/auth/reset-password",
            json={
                "email": "user@example.com"
            }
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset email sent"
        
        # Verify the service was called with correct parameters
        mock_auth_service['reset_password'].assert_called_once_with(
            email="user@example.com"
        )
    
    def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh."""
        # Mock the refresh_token service response
        mock_auth_service['refresh_token'].return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token"
        }
        
        # Send a request to the refresh endpoint
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "old-refresh-token"
            }
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["access_token"] == "new-access-token"
        assert response.json()["refresh_token"] == "new-refresh-token"
        
        # Verify the service was called with correct parameters
        mock_auth_service['refresh_token'].assert_called_once_with(
            refresh_token="old-refresh-token"
        ) 