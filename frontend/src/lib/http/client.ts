import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosError } from 'axios';
import { supabase } from '../supabase'; // Adjust path if needed
import { config } from '@/config';   // For baseURL

const instance: AxiosInstance = axios.create({
  baseURL: config.apiUrl, // Use config.apiUrl for consistency
});

// Request Interceptor to add the auth token
instance.interceptors.request.use(
  async (axiosConfig: InternalAxiosRequestConfig) => {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
      axiosConfig.headers['Authorization'] = `Bearer ${session.access_token}`;
    } else {
      // No session or token, request will proceed without auth header.
      // Backend will return 401 if auth is required.
      console.warn('No active Supabase session or access token found for outgoing request to:', axiosConfig.url);
    }
    return axiosConfig;
  },
  (error: AxiosError) => {
    // Handle request error
    console.error('Axios request error:', error);
    return Promise.reject(error);
  }
);

// Response Interceptor
instance.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // Do something with response data
    return response;
  },
  async (error: AxiosError) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }; // Keep if retry logic is added

    if (error.response?.status === 401) {
      console.warn('Axios request received 401 Unauthorized.');
      // At this point, supabase-js should have tried to auto-refresh if the token was simply expired.
      // A persistent 401 likely means the session is invalid or the refresh token itself expired.

      // Option 1: Trigger a global logout/redirect (more robust)
      // This would ideally be handled by a shared auth context/service that listens for auth errors.
      // For example: authService.handleUnauthorizedError(); which might clear supabase session and redirect.
      // window.dispatchEvent(new Event('supabase-auth-error')); // Example of an event
      // window.location.href = '/login'; // Simplistic redirect

      // Option 2: Try to force a new session check, though less likely to help if already 401
      // This is less reliable if the underlying Supabase session is truly invalid.
      // const { data: { session: newSession } } = await supabase.auth.getSession();
      // if (newSession?.access_token && originalRequest && !originalRequest._retry) {
      //   originalRequest._retry = true;
      //   if(originalRequest.headers) {
      //       originalRequest.headers['Authorization'] = `Bearer ${newSession.access_token}`;
      //   }
      //   return instance(originalRequest);
      // }

      // If we reach here, it's a definitive auth failure.
      // Propagate the error so UI can react (e.g., show login, display error message).
      // Consider clearing any local Supabase session data if appropriate,
      // though Supabase itself should manage its session state.
      // await supabase.auth.signOut(); // Could be too aggressive here, depends on desired UX
      console.error('Authentication required or session expired. Please log in again.');
      // TODO: Implement global auth error handling (e.g., redirect to login, emit event)
    }
    // For other errors, axios already rejects the promise.
    return Promise.reject(error);
  }
);

export default instance;
