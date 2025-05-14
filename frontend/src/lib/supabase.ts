import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Ensure these environment variables are set in your frontend environment
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL; // Or your VITE_ variable e.g. process.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_ANON_KEY; // Or your VITE_ variable e.g. process.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl) {
  throw new Error(
    "Supabase URL is missing. Ensure SUPABASE_URL (or VITE_SUPABASE_URL) is set in your environment variables."
  );
}
if (!supabaseAnonKey) {
  throw new Error(
    "Supabase Anon Key is missing. Ensure ANON_KEY (or VITE_SUPABASE_ANON_KEY) is set in your environment variables."
  );
}

// Create and export the Supabase client instance
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true, 
    persistSession: true,   
    detectSessionInUrl: true 
  },
});

// Helper function to get authenticated headers
export async function getAuthHeaders(contentType?: string | null): Promise<HeadersInit> {
  const { data: { session }, error: sessionError } = await supabase.auth.getSession();

  if (sessionError) {
    console.error('Error getting session:', sessionError);
    throw new Error('Authentication error: Could not get session.');
  }
  if (!session) {
    console.error('No active session found for API call.');
    // This error should ideally be caught by the calling UI/component
    // to trigger a login flow or display an appropriate message.
    throw new Error('Authentication required. Please log in.');
  }
  const accessToken = session.access_token;
  if (!accessToken) {
    console.error('Access token not found in session.');
    throw new Error('Authentication error: Access token missing.');
  }

  const headers: HeadersInit = {
    'Authorization': `Bearer ${accessToken}`
  };
  // Only set Content-Type if it's explicitly provided (not null or undefined)
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  return headers;
}

// export type { User, Session, AuthChangeEvent, AuthError } from '@supabase/supabase-js'; 