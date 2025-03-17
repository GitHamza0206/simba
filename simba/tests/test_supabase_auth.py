import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from simba.auth.supabase_client import SupabaseClientSingleton
from simba.auth.auth_service import AuthService
from simba.core.config import settings

# Skip tests if Supabase credentials are not configured
supabase_credentials_available = bool(settings.supabase.url and settings.supabase.key)

@pytest.fixture
def reset_supabase_client():
    """Reset the Supabase client singleton before and after tests."""
    SupabaseClientSingleton.reset_instance()
    yield
    SupabaseClientSingleton.reset_instance()


@pytest.mark.skipif(
    not supabase_credentials_available,
    reason="Supabase credentials not configured"
)
class TestSupabaseClient:
    """Test Supabase client functionality."""
    
    def test_client_initialization(self, reset_supabase_client):
        """Test that the Supabase client can be initialized."""
        try:
            client = SupabaseClientSingleton.get_instance()
            assert client is not None, "Supabase client should be initialized"
        except Exception as e:
            pytest.fail(f"Supabase client initialization failed: {str(e)}")
    
    def test_singleton_pattern(self, reset_supabase_client):
        """Test that the singleton pattern works correctly."""
        client1 = SupabaseClientSingleton.get_instance()
        client2 = SupabaseClientSingleton.get_instance()
        assert client1 is client2, "Should return the same instance"


class TestAuthServiceMocked:
    """Test Auth Service with mocked Supabase client."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client for testing."""
        with patch('simba.auth.auth_service.get_supabase_client') as mock_get_client:
            # Create mock objects for the Supabase client structure
            mock_auth = MagicMock()
            mock_client = MagicMock()
            mock_client.auth = mock_auth
            
            # Set up the return value for get_supabase_client
            mock_get_client.return_value = mock_client
            
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_sign_up(self, mock_supabase):
        """Test user signup."""
        # Mock the sign_up response
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2023-01-01T00:00:00"
        mock_user.user_metadata = {"role": "user"}
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.error = None
        
        mock_supabase.auth.sign_up.return_value = mock_response
        
        # Call the service method
        result = await AuthService.sign_up(
            email="test@example.com",
            password="password123",
            user_metadata={"role": "user"}
        )
        
        # Verify the result
        assert result["id"] == "test-user-id"
        assert result["email"] == "test@example.com"
        assert result["metadata"] == {"role": "user"}
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_up.assert_called_once_with({
            "email": "test@example.com",
            "password": "password123",
            "options": {
                "data": {"role": "user"}
            }
        })
    
    @pytest.mark.asyncio
    async def test_sign_up_error(self, mock_supabase):
        """Test user signup with error."""
        # Mock the sign_up response with an error
        mock_error = MagicMock()
        mock_error.message = "Email already registered"
        
        mock_response = MagicMock()
        mock_response.error = mock_error
        
        mock_supabase.auth.sign_up.return_value = mock_response
        
        # Call the service method and expect an error
        with pytest.raises(ValueError) as excinfo:
            await AuthService.sign_up(
                email="existing@example.com",
                password="password123"
            )
        
        # Verify the error message
        assert "Failed to sign up: Email already registered" in str(excinfo.value)
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_up.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_up_exception(self, mock_supabase):
        """Test user signup with an exception."""
        # Mock the sign_up method to raise an exception
        mock_supabase.auth.sign_up.side_effect = Exception("Connection failed")
        
        # Call the service method and expect an error
        with pytest.raises(ValueError) as excinfo:
            await AuthService.sign_up(
                email="test@example.com",
                password="password123"
            )
        
        # Verify the error message
        assert "Failed to sign up: Connection failed" in str(excinfo.value)
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_up.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_in(self, mock_supabase):
        """Test user signin."""
        # Mock the sign_in response
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.user_metadata = {"role": "user"}
        
        mock_session = MagicMock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_at = 1672531200  # Example timestamp
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_response.error = None
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        # Call the service method
        result = await AuthService.sign_in(
            email="test@example.com",
            password="password123"
        )
        
        # Verify the result
        assert result["user"]["id"] == "test-user-id"
        assert result["user"]["email"] == "test@example.com"
        assert result["session"]["access_token"] == "test-access-token"
        assert result["session"]["refresh_token"] == "test-refresh-token"
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_in_with_password.assert_called_once_with({
            "email": "test@example.com",
            "password": "password123"
        })
    
    @pytest.mark.asyncio
    async def test_sign_in_error(self, mock_supabase):
        """Test user signin with error."""
        # Mock the sign_in response with an error
        mock_error = MagicMock()
        mock_error.message = "Invalid credentials"
        
        mock_response = MagicMock()
        mock_response.error = mock_error
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        # Call the service method and expect an error
        with pytest.raises(ValueError) as excinfo:
            await AuthService.sign_in(
                email="wrong@example.com",
                password="wrong-password"
            )
        
        # Verify the error message
        assert "Failed to sign in: Invalid credentials" in str(excinfo.value)
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_in_with_password.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_in_exception(self, mock_supabase):
        """Test user signin with an exception."""
        # Mock the sign_in method to raise an exception
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Connection failed")
        
        # Call the service method and expect an error
        with pytest.raises(ValueError) as excinfo:
            await AuthService.sign_in(
                email="test@example.com",
                password="password123"
            )
        
        # Verify the error message
        assert "Failed to sign in: Connection failed" in str(excinfo.value)
        
        # Verify the mock was called correctly
        mock_supabase.auth.sign_in_with_password.assert_called_once() 