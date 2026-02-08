import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { useToast } from '@/hooks/use-toast';
import { tokenStorage } from '@/lib/api';

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
}

interface AuthError {
  message: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName?: string) => Promise<{ error: AuthError | null }>;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signInWithOAuth: (provider: 'google' | 'facebook') => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // Cargar usuario al iniciar
  useEffect(() => {
    const loadUser = async () => {
      const token = tokenStorage.getAccessToken();
      
      if (token) {
        try {
          const response = await fetch(`${API_BASE_URL}${API_VERSION}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            // Token inválido o expirado
            tokenStorage.clearTokens();
          }
        } catch (error) {
          console.error('Error loading user:', error);
          tokenStorage.clearTokens();
        }
      }
      
      setLoading(false);
    };

    loadUser();

    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const refreshToken = urlParams.get('refresh_token');
    
    if (token && refreshToken) {
      tokenStorage.setAccessToken(token);
      tokenStorage.setRefreshToken(refreshToken);
      
      // Remove tokens from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Reload user
      loadUser();
    }
  }, []);

  const signUp = async (email: string, password: string, fullName?: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}${API_VERSION}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          username: email.split('@')[0], // Usar email como username por defecto
          full_name: fullName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const error = { message: data.detail || 'Registration failed' };
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
        return { error };
      }

      toast({
        title: "Success",
        description: "Account created successfully! You can now sign in.",
      });

      return { error: null };
    } catch (error: any) {
      const authError = { message: error.message || 'Registration failed' };
      toast({
        title: "Error",
        description: authError.message,
        variant: "destructive",
      });
      return { error: authError };
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      // FastAPI OAuth2 expects form data with username and password
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}${API_VERSION}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        const error = { message: data.detail || 'Login failed' };
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
        return { error };
      }

      // Guardar tokens
      tokenStorage.setAccessToken(data.access_token);
      if (data.refresh_token) {
        tokenStorage.setRefreshToken(data.refresh_token);
      }

      // Cargar información del usuario
      const userResponse = await fetch(`${API_BASE_URL}${API_VERSION}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        
        toast({
          title: "Welcome back!",
          description: "Signed in successfully",
        });
      }

      return { error: null };
    } catch (error: any) {
      const authError = { message: error.message || 'Login failed' };
      toast({
        title: "Error",
        description: authError.message,
        variant: "destructive",
      });
      return { error: authError };
    }
  };

  const signInWithOAuth = async (provider: 'google' | 'facebook') => {
    try {
      // Redirigir al backend para iniciar el flujo OAuth
      const redirectUrl = `${window.location.origin}/`;
      const oauthUrl = `${API_BASE_URL}${API_VERSION}/auth/oauth/${provider}?redirect_uri=${encodeURIComponent(redirectUrl)}`;
      
      window.location.href = oauthUrl;
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || 'OAuth login failed',
        variant: "destructive",
      });
    }
  };

  const signOut = async () => {
    try {
      // Limpiar tokens
      tokenStorage.clearTokens();
      setUser(null);
      
      toast({
        title: "Signed out",
        description: "See you soon!",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || 'Logout failed',
        variant: "destructive",
      });
    }
  };

  const resetPassword = async (email: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}${API_VERSION}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        const error = { message: data.detail || 'Password reset failed' };
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
        return { error };
      }

      toast({
        title: "Check your email",
        description: "We sent you a password reset link",
      });

      return { error: null };
    } catch (error: any) {
      const authError = { message: error.message || 'Password reset failed' };
      toast({
        title: "Error",
        description: authError.message,
        variant: "destructive",
      });
      return { error: authError };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signUp,
        signIn,
        signInWithOAuth,
        signOut,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
