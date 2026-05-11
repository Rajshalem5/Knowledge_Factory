/**
 * Authentication Context — manages user auth state.
 * Access token in memory (not localStorage — reduces XSS exposure).
 * Refresh token in httpOnly cookie — set by backend, sent automatically.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { authApi } from '../api/auth';
import { tokenStore } from '../api/token';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: RegisterData | FormData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  hasRole: (role: string[]) => boolean;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  college?: string;
  branch?: string;
  cgpa?: number;
  passed_out_year?: number;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => tokenStore.getAccessToken());
  const [isVerifying, setIsVerifying] = useState(false);

  // On mount: try cookie-based refresh for session persistence across reloads
  useEffect(() => {
    const accessToken = tokenStore.getAccessToken();

    if (!accessToken) {
      // No in-memory token — try cookie-based refresh
      authApi.refreshToken()
        .then((refreshRes: any) => {
          if (!refreshRes || !refreshRes.access_token) throw new Error('no refresh');
          return authApi.normalizeTokenResponse(refreshRes as any);
        })
        .then((normalized) => {
          if (normalized) {
            tokenStore.setAccessToken(normalized.token);
            setToken(normalized.token);
            setUser(normalized.user);
          }
        })
        .catch(() => {
          // No cookie either — user needs to log in
        })
        .finally(() => setIsVerifying(false));
      return;
    }

    // Have an in-memory token — verify current session
    authApi.getMe()
      .then((userData) => {
        setUser({
          id: userData.id,
          email: userData.email,
          name: userData.name,
          role: userData.role.toLowerCase() as User['role'],
        });
      })
      .catch(() => {
        // Try refresh as fallback (cookie-based)
        return authApi.refreshToken();
      })
      .then((refreshRes) => {
        if (refreshRes) {
          return authApi.normalizeTokenResponse(refreshRes);
        }
      })
      .then((normalized) => {
        if (normalized) {
          tokenStore.setAccessToken(normalized.token);
          setToken(normalized.token);
          setUser(normalized.user);
        }
      })
      .catch(() => {
        tokenStore.clear();
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsVerifying(false));
  }, []);

  const handleLogout = useCallback(() => {
    tokenStore.clear();
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login({ email, password });
    tokenStore.setAccessToken(response.token);
    setToken(response.token);
    setUser(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (data: RegisterData | FormData) => {
    const response = await authApi.register(data);
    tokenStore.setAccessToken(response.token);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const userData = await authApi.getMe();
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.name,
        role: userData.role.toLowerCase() as User['role'],
      });
    } catch {
      handleLogout();
    }
  }, [token, handleLogout]);

  const logout = useCallback(() => {
    authApi.logout().catch(() => {});
    handleLogout();
  }, [handleLogout]);

  const hasRole = useCallback((roles: string[]): boolean => {
    if (!user) return false;
    const userRole = user.role.toLowerCase().replace('_', '');
    return roles.some(r => r.toLowerCase().replace('_', '') === userRole);
  }, [user]);

  const value: AuthContextValue = {
    user,
    token,
    isLoading: isVerifying,
    isAuthenticated: !!token && !!user,
    login,
    register,
    logout,
    refreshUser,
    hasRole,
  };

  if (isVerifying) {
    return null; // Block render until session is verified
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
