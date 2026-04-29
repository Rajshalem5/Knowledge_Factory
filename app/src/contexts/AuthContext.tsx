/**
 * Authentication Context - Manages user authentication state
 * Handles login, logout, refresh token flow
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
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
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('kf_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() => 
    localStorage.getItem('kf_token')
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Auto-refresh token on mount if exists
  useEffect(() => {
    if (token && !user) {
      refreshUser();
    }
  }, [token]);

  /**
   * Login with credentials
   * Sets token in localStorage and updates user state
   */
  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.login({ email, password });
      
      // Store token and user data
      localStorage.setItem('kf_token', response.access_token);
      localStorage.setItem('kf_user', JSON.stringify(response.user));
      
      setToken(response.access_token);
      setUser(response.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Register new user/candidate
   * Automatically logs in after successful registration
   */
  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    try {
      const response = await authApi.register(data);
      
      // Store token and user data
      localStorage.setItem('kf_token', response.access_token);
      localStorage.setItem('kf_user', JSON.stringify(response.user));
      
      setToken(response.access_token);
      setUser(response.user);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh current user data from server
   */
  const refreshUser = useCallback(async () => {
    if (!token) return;
    
    setIsLoading(true);
    try {
      const userData = await authApi.getMe();
      
      const updatedUser: User = {
        id: userData.id,
        email: userData.email,
        name: userData.name,
        role: userData.role as any,
      };
      
      setUser(updatedUser);
      localStorage.setItem('kf_user', JSON.stringify(updatedUser));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // Token might be invalid, clear it
      handleLogout();
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  /**
   * Logout - clears local storage and state
   */
  const logout = useCallback(() => {
    // Call logout API (optional - mostly for audit trail)
    authApi.logout()
      .catch(err => console.warn('Logout API call failed:', err))
      .finally(() => {
        handleLogout();
      });
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('kf_token');
    localStorage.removeItem('kf_user');
    setToken(null);
    setUser(null);
  }, []);

  /**
   * Check if user has one of the specified roles
   */
  const hasRole = useCallback((roles: string[]): boolean => {
    if (!user) return false;
    const userRole = user.role.toLowerCase().replace('_', '');
    return roles.some(r => r.toLowerCase().replace('_', '') === userRole);
  }, [user]);

  const value: AuthContextValue = {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    login,
    register,
    logout,
    refreshUser,
    hasRole,
  };

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
