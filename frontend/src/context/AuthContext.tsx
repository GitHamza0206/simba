import React, { createContext, useContext, useEffect, useState } from 'react';
import { signIn, signOut, signUp, resetPassword, isAuthenticated, getAccessToken, refreshToken } from '@/lib/supabase';
import { Navigate } from 'react-router-dom';

// Define the User type
type User = {
  id: string;
  email: string;
  metadata?: Record<string, any>;
};

// Define the AuthContext type
interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, userData?: Record<string, any>) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  clearError: () => void;
}

// Create the Auth Context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Check auth status on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      setLoading(true);
      try {
        // Check if we have a token in localStorage
        const token = localStorage.getItem('accessToken');
        const userId = localStorage.getItem('userId');
        const userEmail = localStorage.getItem('userEmail');
        
        console.log('Auth check:', { 
          hasToken: !!token, 
          userId, 
          userEmail,
          isAuthenticated: isAuthenticated()
        });
        
        if (isAuthenticated() && userId && userEmail) {
          try {
            // Attempt to refresh the token
            await refreshToken();
            
            setUser({
              id: userId,
              email: userEmail,
            });
            console.log('User authenticated:', { id: userId, email: userEmail });
          } catch (err) {
            // If refresh fails, clear any stored auth data
            console.error('Token refresh failed:', err);
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('userEmail');
            setUser(null);
          }
        } else {
          // If we're missing any data, clear everything to be safe
          if (token && (!userId || !userEmail)) {
            console.warn('Incomplete auth data, clearing storage');
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('userEmail');
          }
          setUser(null);
        }
      } catch (err) {
        console.error('Auth check error:', err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Sign In handler
  const handleSignIn = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await signIn(email, password);
      console.log('Sign in successful, setting user:', data.user);
      setUser(data.user);
    } catch (err: any) {
      console.error('Sign in error in context:', err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Sign Up handler
  const handleSignUp = async (email: string, password: string, userData?: Record<string, any>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await signUp(email, password, userData);
      // Note: For most auth systems, you'd still need to sign in after sign up
      // But for simplicity, we'll just set the user
      setUser(data);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Sign Out handler
  const handleSignOut = async () => {
    setLoading(true);
    setError(null);
    try {
      await signOut();
      setUser(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Reset Password handler
  const handleResetPassword = async (email: string) => {
    setLoading(true);
    setError(null);
    try {
      await resetPassword(email);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Clear error
  const clearError = () => setError(null);

  // Create context value
  const value = {
    user,
    loading,
    error,
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    resetPassword: handleResetPassword,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Protected route component
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  const [redirecting, setRedirecting] = useState(false);
  
  useEffect(() => {
    if (!loading && !user) {
      console.log('ProtectedRoute: User not authenticated, redirecting to login');
      setRedirecting(true);
    }
  }, [loading, user]);
  
  // Show loading state while checking authentication
  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading authentication status...</div>;
  }
  
  // Show redirecting message
  if (redirecting) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="mb-4">You need to be logged in to view this page.</p>
        <p>Redirecting to login page...</p>
        <Navigate to="/auth/login" replace />
      </div>
    );
  }
  
  // Redirect to login if not authenticated
  if (!user) {
    console.log('ProtectedRoute: User not authenticated but not redirecting yet');
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="mb-4">Authentication check failed.</p>
        <p>Please try refreshing the page or logging in again.</p>
        <button 
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
          onClick={() => window.location.href = '/auth/login'}
        >
          Go to Login
        </button>
      </div>
    );
  }
  
  // Render children if authenticated
  console.log('ProtectedRoute: User authenticated, rendering children');
  return <>{children}</>;
}; 