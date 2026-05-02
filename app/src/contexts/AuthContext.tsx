/**
 * Authentication Context — manages user auth state.
 * Access token in memory (not localStorage — reduces XSS exposure).
 * Refreshes via /auth/me on mount. Supports silent 401 refresh via api client.
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
  login: (email: string, password: string) => Promise<void>;
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
  const [isVerifying, setIsVerifying] = useState(!!tokenStore.getRefreshToken());

  // On mount: verify session exists via /auth/me
  useEffect(() => {
    const refreshToken = tokenStore.getRefreshToken();
    const accessToken = tokenStore.getAccessToken();

    if (!refreshToken && !accessToken) {
      // Microtask avoids sync setState in effect body
      queueMicrotask(() => setIsVerifying(false));
      return;
    }

    // If we have a refresh token but no access token, try refreshing
    if (refreshToken && !accessToken) {
      authApi.refreshToken(refreshToken)
        .then(async (res) => {
          const { token: tkn, user: usr } = await authApi.normalizeTokenResponse(res);
          tokenStore.setAccessToken(tkn);
          tokenStore.setRefreshToken(res.refresh_token);
          setToken(tkn);
          setUser(usr);
        })
        .catch(() => {
          tokenStore.clear();
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsVerifying(false));
      return;
    }

    // Verify current session
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
        // Try refresh as fallback
        if (refreshToken) {
          return authApi.refreshToken(refreshToken);
        }
        throw new Error('Session invalid');
      })
      .then((refreshRes) => {
        if (refreshRes) {
          return authApi.normalizeTokenResponse(refreshRes);
        }
      })
      .then((normalized) => {
        if (normalized) {
          tokenStore.setAccessToken(normalized.token);
          tokenStore.setRefreshToken(normalized.token); // will be set by normalizeTokenResponse
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
    tokenStore.setRefreshToken(response.refresh_token);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData | FormData) => {
    const response = await authApi.register(data);
    tokenStore.setAccessToken(response.token);
    tokenStore.setRefreshToken(response.refresh_token);
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
