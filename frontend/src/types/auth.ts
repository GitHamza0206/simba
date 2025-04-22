export interface AuthResponse {
  user: User;
  session: Session;
}

export interface User {
  id: string;
  email: string;
  role?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface Session {
  access_token: string;
  refresh_token: string;
  expires_at?: number;
}

export interface SignUpCredentials {
  email: string;
  password: string;
  metadata?: Record<string, any>;
}

export interface SignInCredentials {
  email: string;
  password: string;
}

export interface AuthError {
  message: string;
  status?: number;
} 