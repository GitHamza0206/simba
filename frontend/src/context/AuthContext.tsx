import React, { createContext, useContext, useEffect, useState } from 'react';
// import { signIn, signOut, signUp, resetPassword, isAuthenticated, getAccessToken, refreshToken } from '@/lib/supabase'; // OLD
import { supabase } from '@/lib/supabase'; // NEW
// import { AuthError, User as SupabaseUser } from '@supabase/supabase-js'; // NEW - Keep AuthError and SupabaseUser for potential direct use or more specific typing later
import { AuthError } from '@supabase/supabase-js'; // NEW - SupabaseUser was unused
import { Navigate } from 'react-router-dom';

// Define the User type - aligning more with SupabaseUser
type User = {
  id: string;
  email?: string; // Supabase user email can be undefined
  // metadata?: Record<string, any>; // OLD - will use SupabaseUser's app_metadata and user_metadata if needed
  app_metadata?: Record<string, unknown>; // Use unknown instead of any
  user_metadata?: Record<string, unknown>; // Use unknown instead of any
};

// Define the AuthContext type
interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, userData?: Record<string, unknown>) => Promise<void>; // Use unknown
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

  // Check auth status on mount and listen for changes
  useEffect(() => {
    setLoading(true);

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session && session.user) {
        setUser({
          id: session.user.id,
          email: session.user.email,
          app_metadata: session.user.app_metadata,
          user_metadata: session.user.user_metadata,
        });
      } else {
        setUser(null);
      }
      setLoading(false);
    }).catch((err) => {
        console.error("Error getting session:", err);
        setUser(null);
        setLoading(false);
    });

    // Listen for auth state changes
    const { data: { subscription: authSubscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth event:', event, session);
        if (session && session.user) {
          setUser({
            id: session.user.id,
            email: session.user.email,
            app_metadata: session.user.app_metadata,
            user_metadata: session.user.user_metadata,
          });
        } else {
          setUser(null);
        }
        // setLoading(false); // Typically only set loading false after initial check
      }
    );

    // Cleanup listener on component unmount
    return () => {
      authSubscription?.unsubscribe();
    };
  }, []);

  // Sign In handler
  const handleSignIn = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error: supaError } = await supabase.auth.signInWithPassword({ email, password });
      if (supaError) throw supaError;
      // The onAuthStateChange listener will handle setting the user state
      console.log('Sign in successful, session data:', data.session);
      // If direct user setting is needed (though onAuthStateChange should cover it):
      // if (data.user) {
      //   setUser({
      //     id: data.user.id,
      //     email: data.user.email,
      //     app_metadata: data.user.app_metadata,
      //     user_metadata: data.user.user_metadata,
      //   });
      // }
    } catch (err: unknown) {
      const authErr = err as AuthError;
      console.error('Sign in error in context:', authErr);
      setError(authErr.message);
      throw authErr; // Re-throw the original Supabase error or a new error
    } finally {
      setLoading(false);
    }
  };

  // Sign Up handler
  const handleSignUp = async (email: string, password: string, userData?: Record<string, unknown>) => { // Use unknown
    setLoading(true);
    setError(null);
    try {
      const { data, error: supaError } = await supabase.auth.signUp({
        email,
        password,
        options: { data: userData },
      });
      if (supaError) throw supaError;
      // The onAuthStateChange listener will typically handle setting the user state upon email confirmation / login
      // Supabase signUp might return a user if auto-confirm is on and session is created, or if session exists
      console.log('Sign up call successful, data:', data);
      if (data.user) {
         setUser({ // Optimistically set user, or rely on onAuthStateChange
           id: data.user.id,
           email: data.user.email,
           app_metadata: data.user.app_metadata,
           user_metadata: data.user.user_metadata,
         });
      }
      // Depending on your Supabase settings (e.g. email confirmation), 
      // the user might not be immediately active or have a session.
      // You might want to inform the user to check their email.
    } catch (err: unknown) {
      const authErr = err as AuthError;
      setError(authErr.message);
      throw authErr;
    } finally {
      setLoading(false);
    }
  };

  // Sign Out handler
  const handleSignOut = async () => {
    setLoading(true);
    setError(null);
    try {
      const { error: supaError } = await supabase.auth.signOut();
      if (supaError) throw supaError;
      // The onAuthStateChange listener will handle setting user to null
    } catch (err: unknown) {
      const authErr = err as AuthError;
      setError(authErr.message);
      throw authErr;
    } finally {
      setLoading(false);
    }
  };

  // Reset Password handler
  const handleResetPassword = async (email: string) => {
    setLoading(true);
    setError(null);
    try {
      const { error: supaError } = await supabase.auth.resetPasswordForEmail(email, {
        // redirectTo: 'http://localhost:5173/update-password', // Optional: URL to redirect to after email link click
      });
      if (supaError) throw supaError;
      // Inform the user to check their email
    } catch (err: unknown) {
      const authErr = err as AuthError;
      setError(authErr.message);
      throw authErr;
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