import os
import uuid
from simba_sdk import SimbaClient

def create_key():
    """
    Signs up a new user, signs in, and creates a new API key.
    """
    api_url = os.environ.get("SIMBA_API_URL", "http://0.0.0.0:5005")
    client = SimbaClient(api_url=api_url)

    # 1. Create a new user for the test
    unique_id = str(uuid.uuid4())
    email = f"key-creator-{unique_id}@example.com"
    password = "a_very_secure_password_123"
    
    print(f"--- Attempting to sign up user: {email} ---")
    try:
        client.auth.signup(email=email, password=password)
        print("Sign-up successful.")
    except Exception as e:
        print(f"Sign-up failed: {e}")
        print("Please ensure your Simba server is running and accessible.")
        return

    # 2. Sign in to get a session token
    print(f"--- Attempting to sign in user: {email} ---")
    try:
        client.auth.signin(email=email, password=password)
        print("Sign-in successful. Client now has a session token.")
    except Exception as e:
        print(f"Sign-in failed: {e}")
        return

    # 3. Create a new API key using the authenticated session
    print("--- Attempting to create a new API key ---")
    try:
        # The create_key endpoint is not yet in the SDK, so we call it directly.
        # This assumes the endpoint is POST /api_keys
        key_name = f"My Test Key {unique_id[:8]}"
        response = client._make_request(
            "POST",
            "/api/api-keys",
            json={
                "name": key_name,
                "roles": ["user"], # Assign default roles
            }
        )
        new_api_key = response.get("key")
        if new_api_key:
            print("\n🎉 --- API Key Created Successfully! --- 🎉")
            print(f"Your new API key is:\n")
            print(new_api_key)
            print("\nCopy this key and update your `auth_test.py` script or environment variables.")
        else:
            print("Failed to create API key. Response did not contain a key.")
            print("Response from server:", response)
            
    except Exception as e:
        print(f"API key creation failed: {e}")
        print("Please check the server logs for more details.")

if __name__ == "__main__":
    create_key() 