import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosError, AxiosResponse } from 'axios';

// Define the shape of the functions we need from the auth service
interface AuthFunctions {
  getAccessToken: () => string | null;
  refreshToken: () => Promise<string>;
  onAuthError: () => void; // Function to call when refresh fails
}

export function createAuthAxiosInstance({ 
  getAccessToken, 
  refreshToken, 
  onAuthError 
}: AuthFunctions): AxiosInstance {
  
  const authAxios = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  });

  // Request interceptor to add the access token
  authAxios.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getAccessToken();
      if (token) {
        console.log('Adding auth header with token:', token.substring(0, 10) + '...');
        config.headers['Authorization'] = `Bearer ${token}`;
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
    (error: AxiosError) => Promise.reject(error)
  );

  // Response interceptor for token refresh
  authAxios.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // If error is 401 and we haven't retried yet
      if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          console.log('Attempting to refresh token after 401 error');
          // Try to refresh the token
          await refreshToken(); 
          
          // Token should be updated in localStorage by refreshToken
          // Re-fetch the token for the retry
          const newToken = getAccessToken();
          if (newToken && originalRequest.headers) {
             originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          }
          
          // Retry the original request with the new token in the header
          return authAxios(originalRequest);
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          // Call the callback to handle auth error (e.g., redirect to login)
          onAuthError(); 
          return Promise.reject(refreshError);
        }
      }
      
      return Promise.reject(error);
    }
  );

  return authAxios;
} 