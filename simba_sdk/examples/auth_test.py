import os
import uuid
from simba_sdk import SimbaClient

def main():
    # Initialize SimbaClient from environment variables
    # For auth operations, you don't need an API key to start

    api_url = os.environ.get("SIMBA_API_URL")
    api_key = os.environ.get("SIMBA_API_KEY")
    
    client = SimbaClient(api_url=api_url, api_key=api_key)

    # Generate a unique email for a new user to avoid conflicts
    unique_id = str(uuid.uuid4())
    email = f"testuser_{unique_id}@example.com"
    password = "a_strong_password"

    print("--- Testing Authentication Flow ---")

    # 1. Sign up a new user
    try:
        print(f"Attempting to sign up user: {email}")
        signup_response = client.auth.signup(email=email, password=password)
        print("Sign-up successful!")
        # print("Sign-up response:", signup_response)
    except Exception as e:
        print(f"Sign-up failed: {e}")
        return

    # 2. Sign in with the new user
    try:
        print(f"Attempting to sign in user: {email}")
        signin_response = client.auth.signin(email=email, password=password)
        print("Sign-in successful!")
        # print("Sign-in response:", signin_response)
        
        # The client now stores session information automatically
        # The access_token is automatically added to headers for subsequent requests
        
    except Exception as e:
        print(f"Sign-in failed: {e}")
        return

    # 3. Get current user's profile
    try:
        print("Fetching current user's profile (/me)...")
        me_response = client.auth.me()
        print("Successfully fetched user profile:")
        print("User ID:", me_response.get("id"))
        print("User Email:", me_response.get("email"))
    except Exception as e:
        print(f"Failed to fetch user profile: {e}")

    # 4. Sign out the user
    try:
        print("Attempting to sign out...")
        signout_response = client.auth.signout()
        print("Sign-out successful!")
        # print("Sign-out response:", signout_response)
        
        # The client's session is now cleared
        
    except Exception as e:
        print(f"Sign-out failed: {e}")
        
    # Example of what happens when you call an authenticated endpoint after signing out
    try:
        print("\nAttempting to fetch user profile again (should fail)...")
        client.auth.me()
    except Exception as e:
        print(f"Request failed as expected after sign-out: {e}")

if __name__ == "__main__":
    main() 