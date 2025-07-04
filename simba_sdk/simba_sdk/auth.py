from typing import Dict, Any, Optional

class AuthManager:
    """
    A class that provides authentication functionality for the Simba SDK.
    Handles user signup, signin, signout, and other auth-related operations.
    """

    def __init__(self, client):
        """
        Initialize the AuthManager with a SimbaClient instance.
        
        Args:
            client: An instance of SimbaClient
        """
        self.client = client
        
    def signup(self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email (str): The user's email.
            password (str): The user's password.
            metadata (Optional[Dict[str, Any]]): Additional user metadata.
            
        Returns:
            Dict[str, Any]: The response from the server, typically user information.
        """
        payload = {"email": email, "password": password}
        if metadata:
            payload["metadata"] = metadata
            
        return self.client._make_request(
            "POST",
            "auth/signup",
            json=payload
        )

    def signin(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user.
        
        Args:
            email (str): The user's email.
            password (str): The user's password.
            
        Returns:
            Dict[str, Any]: The response from the server, including session tokens.
        """
        payload = {"email": email, "password": password}
        response = self.client._make_request(
            "POST",
            "auth/signin",
            json=payload
        )
        
        if "session" in response and "access_token" in response["session"]:
            self.client.session = response["session"]
            access_token = response["session"]["access_token"]
            self.client.headers["Authorization"] = f"Bearer {access_token}"
            # Prioritize JWT, so remove API key from headers if it exists
            if "X-API-Key" in self.client.headers:
                del self.client.headers["X-API-Key"]
            
        return response

    def signout(self) -> Dict[str, Any]:
        """
        Sign out the current user.
        """
        response = self.client._make_request(
            "POST",
            "auth/signout"
        )
        # Clear session data on the client side
        self.client.session = None
        if "Authorization" in self.client.headers:
            del self.client.headers["Authorization"]

        # Restore API key if it was originally provided
        if self.client.api_key:
            self.client.headers["X-API-Key"] = self.client.api_key
            
        return response

    def reset_password(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset for a user.
        
        Args:
            email (str): The email of the user to reset the password for.
            
        Returns:
            Dict[str, Any]: A confirmation message.
        """
        return self.client._make_request(
            "POST",
            "auth/reset-password",
            json={"email": email}
        )

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh the session using a refresh token.
        
        Args:
            refresh_token (str): The refresh token.
            
        Returns:
            Dict[str, Any]: New session information, including a new access token.
        """
        response = self.client._make_request(
            "POST",
            "auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if "session" in response and "access_token" in response["session"]:
            self.client.session = response["session"]
            access_token = response["session"]["access_token"]
            self.client.headers["Authorization"] = f"Bearer {access_token}"
            
        return response

    def me(self) -> Dict[str, Any]:
        """
        Get the profile of the currently authenticated user.
        
        Returns:
            Dict[str, Any]: The user's profile information.
        """
        return self.client._make_request(
            "GET",
            "auth/me"
        ) 