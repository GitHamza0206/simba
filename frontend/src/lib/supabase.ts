import axios from 'axios';
import { 
  AuthResponse, 
  SignInCredentials, 
  SignUpCredentials, 
  User 
} from '@/types/auth';

// Base API URL for auth operations
const API_URL = import.meta.env.VITE_API_URL ;

// Sign up with email and password
export async function signUp(
  email: string, 
  password: string, 
  userData?: Record<string, any>
): Promise<User> {
  try {
    const payload: SignUpCredentials = {
      email,
      password,
      metadata: userData,
    };
    
    const response = await axios.post(`${API_URL}/auth/signup`, payload);
    
    // If signup was successful, also store the user data
    if (response.data && response.data.user) {
      localStorage.setItem('userId', response.data.user.id);
      localStorage.setItem('userEmail', response.data.user.email);
    }
    
    return response.data.user;
  } catch (error: any) {
    console.error('Sign up error:', error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to sign up');
  }
}

// Sign in with email and password
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  try {
    const payload: SignInCredentials = {
      email,
      password,
    };
    
    console.log('Signing in with:', payload);
    const response = await axios.post(`${API_URL}/auth/signin`, payload);
    console.log('Sign in response:', response.data);
    
    const data = response.data;
    
    // Make sure we have a valid session structure
    if (!data || !data.session || !data.user) {
      console.error('Invalid auth response structure:', data);
      throw new Error('Invalid authentication response from server');
    }
    
    // Store tokens in localStorage
    localStorage.setItem('accessToken', data.session.access_token);
    localStorage.setItem('refreshToken', data.session.refresh_token);
    
    // Also store user information
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('userEmail', data.user.email);
    
    // Debug: Verify token was stored
    console.log('Stored access token:', data.session.access_token.substring(0, 10) + '...');
    
    return data;
  } catch (error: any) {
    console.error('Sign in error:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || error.response?.data?.message || 'Failed to sign in');
  }
}

// Sign out
export async function signOut(): Promise<void> {
  try {
    await axios.post(`${API_URL}/auth/signout`, {}, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`
      }
    });
    
    // Clear tokens and user data from localStorage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
  } catch (error: any) {
    console.error('Sign out error:', error.response?.data || error.message);
    // Clear tokens and user data even if the API call fails
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    throw new Error(error.response?.data?.message || 'Failed to sign out');
  }
}

// Reset password
export async function resetPassword(email: string): Promise<void> {
  try {
    await axios.post(`${API_URL}/auth/reset-password`, { email });
  } catch (error: any) {
    console.error('Reset password error:', error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to reset password');
  }
}

// Refresh token
export async function refreshToken(): Promise<string> {
  try {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    console.log('Refreshing token with:', refreshToken.substring(0, 10) + '...');
    const response = await axios.post(`${API_URL}/auth/refresh`, { 
      refresh_token: refreshToken 
    });
    
    console.log('Refresh token response:', response.data);
    const { access_token, refresh_token } = response.data;
    
    // Update tokens in localStorage
    localStorage.setItem('accessToken', access_token);
    localStorage.setItem('refreshToken', refresh_token);
    
    return access_token;
  } catch (error: any) {
    console.error('Refresh token error:', error.response?.data || error.message);
    // Clear tokens if refresh fails
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    throw new Error(error.response?.data?.message || 'Failed to refresh token');
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

// Create axios instance with auth header
export const authAxios = axios.create({
  baseURL: import.meta.env.VITE_API_URL, // Removed API_URL to avoid double prefixing
});

// Add a request interceptor to include the access token
authAxios.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      console.log('Adding auth header with token:', token.substring(0, 10) + '...');
      // Fix: Use the correct Authorization header format expected by FastAPI
      config.headers['Authorization'] = `Bearer ${token}`;
      
      // Debug: Log the full request configuration
      console.log('Request config:', {
        url: config.url,
        method: config.method,
        headers: config.headers,
      });
    } else {
      console.warn('No auth token available for request:', config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
authAxios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 (Unauthorized) and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.log('Attempting to refresh token after 401 error');
        // Try to refresh the token - this will update cookies server-side
        await refreshToken();
        
        // Just retry the request - cookies will be sent automatically
        return authAxios(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // If refresh fails, redirect to login
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
); 