import httpClient from './http/client';
import { 
  AuthResponse, 
  SignInCredentials, 
  SignUpCredentials, 
  User 
} from '@/types/auth';

// Function to handle authentication errors (e.g., redirect to login)
function handleAuthError() {
  // Clear potentially stale auth data
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('userId');
  localStorage.removeItem('userEmail');
  // Redirect to login page
  if (typeof window !== 'undefined') { // Ensure this runs only in the browser
     console.error("Authentication error, redirecting to login.");
     window.location.href = '/auth/login'; 
  } else {
     console.error("Authentication error occurred in non-browser environment.");
  }
}

// Sign up with email and password
export async function signUp(
  email: string, 
  password: string, 
  userData?: Record<string, unknown>
): Promise<User> {
  try {
    const payload: SignUpCredentials = {
      email,
      password,
      metadata: userData,
    };
    
    const response = await httpClient.post(`/auth/signup`, payload);
    
    // If signup was successful, also store the user data
    if (response.data && response.data.user) {
      localStorage.setItem('userId', response.data.user.id);
      localStorage.setItem('userEmail', response.data.user.email);
    }
    
    return response.data.user;
  } catch (error: unknown) {
    let errorMessage = 'Failed to sign up';
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
}

// Sign in with email and password
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  try {
    const payload: SignInCredentials = {
      email,
      password,
    };
    
    const response = await httpClient.post(`/auth/signin`, payload);
    const data = response.data;
    
    // Make sure we have a valid session structure
    if (!data || !data.session || !data.user) {
      throw new Error('Invalid authentication response from server');
    }
    
    // Store tokens in localStorage
    localStorage.setItem('accessToken', data.session.access_token);
    localStorage.setItem('refreshToken', data.session.refresh_token);
    
    // Also store user information
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('userEmail', data.user.email);
    
    return data;
  } catch (error: unknown) {
    let errorMessage = 'Failed to sign in';
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
}

// Sign out
export async function signOut(): Promise<void> {
  try {
    await httpClient.post(`/auth/signout`);
  } finally {
    // Always clear tokens and user data from localStorage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
  }
}

// Reset password
export async function resetPassword(email: string): Promise<void> {
  try {
    await httpClient.post(`/auth/reset-password`, { email });
  } catch (error: unknown) {
    let errorMessage = 'Failed to reset password';
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
}

// Get the current access token from localStorage
export function getAccessToken(): string | null {
  return localStorage.getItem('accessToken');
}

// Check if the user is authenticated
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// Refresh token function
export async function refreshToken(): Promise<string> {
  const currentRefreshToken = localStorage.getItem('refreshToken');
  if (!currentRefreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await httpClient.post(`/auth/refresh`, {
      refresh_token: currentRefreshToken
    });

    const { access_token, refresh_token: new_refresh_token } = response.data;
    
    if (!access_token || !new_refresh_token) {
      throw new Error("Invalid token refresh response");
    }
    
    // Update tokens in localStorage
    localStorage.setItem('accessToken', access_token);
    localStorage.setItem('refreshToken', new_refresh_token);
    
    return access_token;
  } catch (error: unknown) {
    let errorMessage = 'Failed to refresh token';
    if (error instanceof Error) {
      errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
}

// --- Axios Instance Setup ---
// Create the authenticated Axios instance using the factory function
// Pass the necessary functions from this module
export const authAxios = {
  getAccessToken,
  refreshToken: async () => {
    const currentRefreshToken = localStorage.getItem('refreshToken');
    if (!currentRefreshToken) {
      // If there's no refresh token, we can't refresh. 
      // Throwing an error here will be caught by the interceptor's catch block,
      // which will then call handleAuthError (our onAuthError callback).
      console.error('Attempted to refresh token, but none was found.');
      throw new Error('No refresh token available'); 
    }

    try {
      console.log('Refreshing token with:', currentRefreshToken.substring(0, 10) + '...');
      // Use standard axios for the refresh endpoint itself to avoid interceptor loops
      const response = await httpClient.post(`/auth/refresh`, { 
        refresh_token: currentRefreshToken 
      });
      
      console.log('Refresh token response:', response.data);
      const { access_token, refresh_token: new_refresh_token } = response.data;

      if (!access_token || !new_refresh_token) {
        console.error("Invalid token refresh response structure:", response.data);
        throw new Error("Invalid token refresh response"); // Caught below
      }
      
      // Update tokens in localStorage
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', new_refresh_token); // Store the potentially new refresh token
      console.log('Tokens refreshed successfully.');
      
      return access_token; // Return the new access token
    } catch (error: unknown) {
      console.error('Refresh token API call failed.'); // Log specific error before throwing
      let errorMessage = 'Failed to refresh token via API';
      if (error instanceof Error) {
          errorMessage = error.message;
          console.error('Refresh token error:', error.message);
      }
      // Re-throw the error. This will be caught by the response interceptor's catch block,
      // which will then call handleAuthError (our onAuthError callback) because the refresh failed.
      throw new Error(errorMessage); 
    }
  },
  onAuthError: handleAuthError
}; 