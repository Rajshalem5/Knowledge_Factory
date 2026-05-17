/**
 * Authentication Context — manages user auth state.
 * Uses Clerk as the primary auth provider and syncs user data
 * with the Knowledge Factory backend for role management.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { useAuth as useClerkAuth, useUser, useClerk } from '@clerk/react';
import type { User } from '../types';
import { authApi } from '../api/auth';
import { tokenStore } from '../api/token';

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
  college: string;
  branch: string;
  cgpa: number;
  passed_out_year: number;
  language_choice: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded: clerkLoaded, isSignedIn, getToken } = useClerkAuth();
  const { user: clerkUser } = useUser();
  const { signOut } = useClerk();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(true);

  // Sync Clerk auth state → local user state
  useEffect(() => {
    if (!clerkLoaded) return;

    if (!isSignedIn || !clerkUser) {
      setUser(null);
      setToken(null);
      tokenStore.clear();
      setIsVerifying(false);
      return;
    }

    // Get role from Clerk user's public metadata
    const role = clerkUser.publicMetadata?.role as string | undefined;

    // Fall back to fetching user profile from KF backend if no role in metadata
    const activeUser = clerkUser; // captured at effect time, non-null here
    async function syncUser() {
      try {
        const clerkToken = await getToken();
        if (!clerkToken || !activeUser) {
          setUser(null);
          setIsVerifying(false);
          return;
        }

        // Store the Clerk token for API calls
        tokenStore.setAccessToken(clerkToken);
        setToken(clerkToken);

        if (role) {
          setUser({
            id: activeUser.id,
            email: activeUser.primaryEmailAddress?.emailAddress || '',
            name: activeUser.fullName || activeUser.username || 'User',
            role: role.toLowerCase() as User['role'],
          });
        } else {
          // Fetch user profile from the KF backend to get role
          const userData = await authApi.getMe();
          setUser({
            id: userData.id,
            email: userData.email,
            name: userData.name,
            role: userData.role.toLowerCase() as User['role'],
          });
        }
      } catch {
        setUser(null);
        setToken(null);
        tokenStore.clear();
      } finally {
        setIsVerifying(false);
      }
    }

    syncUser();
  }, [clerkLoaded, isSignedIn, clerkUser, getToken]);

  const handleLogout = useCallback(() => {
    tokenStore.clear();
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    // Use Clerk's sign-in via the prebuilt UI instead
    // This path is kept for backward compatibility
    const response = await authApi.login({ email, password });
    tokenStore.setAccessToken(response.token);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    // Use Clerk's sign-up via the prebuilt UI instead
    // This path is kept for backward compatibility
    const response = await authApi.register(data);
    tokenStore.setAccessToken(response.token);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const clerkToken = await getToken();
      if (clerkToken) {
        tokenStore.setAccessToken(clerkToken);
        setToken(clerkToken);
      }

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
  }, [token, getToken, handleLogout]);

  const logout = useCallback(() => {
    signOut();
    authApi.logout().catch(() => {});
    handleLogout();
  }, [signOut, handleLogout]);

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

  if (isVerifying && clerkLoaded) {
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
