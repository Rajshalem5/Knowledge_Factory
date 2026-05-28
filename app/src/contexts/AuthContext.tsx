/**
 * Authentication Context — manages user auth state.
 * Uses Clerk as the primary auth provider and syncs user data
 * with the Knowledge Factory backend for role management.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { authApi } from '../api/auth';
import { tokenStore } from '../api/token';
import { normalizeRole } from '../utils/roles';

// Lazy Clerk hooks — dynamic import so Vite pre-bundles @clerk/react but
// runtime failures (blocked CDN) don't crash the app.
let clerkModule: any = null;
const clerkPromise = import('@clerk/react').then(m => { clerkModule = m; }).catch(() => {
  console.warn('[AuthContext] Clerk SDK unavailable — using JWT auth only');
});
function useSafeClerkAuth() {
  if (!clerkModule) return { isLoaded: true, isSignedIn: false, getToken: async () => null };
  try { return clerkModule.useAuth(); } catch { return { isLoaded: true, isSignedIn: false, getToken: async () => null }; }
}
function useSafeUser() {
  if (!clerkModule) return { user: null };
  try { return clerkModule.useUser(); } catch { return { user: null }; }
}
function useSafeClerk() {
  if (!clerkModule) return { signOut: () => {} };
  try { return clerkModule.useClerk(); } catch { return { signOut: () => {} }; }
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isVerifying: boolean;
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
  const { isLoaded: clerkLoaded, isSignedIn, getToken } = useSafeClerkAuth();
  const { user: clerkUser } = useSafeUser();
  const { signOut } = useSafeClerk();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => tokenStore.getAccessToken());
  const [isVerifying, setIsVerifying] = useState(true);

  // On mount: try cookie-based refresh for session persistence across reloads
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let settled = false;

    const forceUnverified = () => {
      if (!settled) {
        settled = true;
        console.log('[AuthContext] Session verification timed out after 5s — treating as unauthenticated');
        setIsVerifying(false);
      }
    };

    // 5-second safety timeout: if backend is unreachable, unblock the UI
    timeoutId = setTimeout(forceUnverified, 5000);

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
        .finally(() => {
          clearTimeout(timeoutId);
          if (!settled) {
            settled = true;
            setIsVerifying(false);
          }
        });
      return;
    }

    // Have an in-memory token — verify current session
    authApi.getMe()
      .then((userData) => {
        const role = normalizeRole(userData.role);
        console.log(`[AuthContext] getMe success: id=${userData.id}, email=${userData.email}, rawRole=${userData.role}, normalizedRole=${role}`);
        setUser({
          id: userData.id,
          email: userData.email,
          name: userData.name,
          role,
        });
      })
      .catch(() => {
        // Try refresh as fallback (cookie-based)
        return authApi.refreshToken();
      })
      .then(async (refreshRes) => {
        if (refreshRes) {
          return authApi.normalizeTokenResponse(refreshRes);
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
      })
      .catch((_err) => {
        setUser(null);
      })
      .finally(() => {
        clearTimeout(timeoutId);
        if (!settled) {
          settled = true;
          setIsVerifying(false);
        }
      });
  }, []);

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
    console.log(`[AuthContext] login: User set with role=${response.user.role}`);
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
      const clerkToken = await getToken();
      if (clerkToken) {
        tokenStore.setAccessToken(clerkToken);
        setToken(clerkToken);
      }

      const userData = await authApi.getMe();
      const role = normalizeRole(userData.role);
      console.log(`[AuthContext] refreshUser: rawRole=${userData.role}, normalizedRole=${role}`);
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.name,
        role,
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
    const userRole = normalizeRole(user.role);
    const normalizedAllowed = roles.map(r => normalizeRole(r));
    const hasMatch = normalizedAllowed.includes(userRole);
    console.log(`[Auth] hasRole: UserRole=${userRole} (raw: ${user.role}), Allowed=[${normalizedAllowed.join(', ')}] (raw: [${roles.join(', ')}]). Result=${hasMatch}`);
    return hasMatch;
  }, [user]);

  const value: AuthContextValue = {
    user,
    token,
    isLoading: isVerifying,
    isVerifying,
    isAuthenticated: !!token && !!user,
    login,
    register,
    logout,
    refreshUser,
    hasRole,
  };

  // Diagnostic: log auth state changes
  console.log(`[AuthContext] isVerifying=${isVerifying}, user=${user?.email}, loading=${isVerifying}`);

  // Always render children — public routes must not be blocked during verification.
  // ProtectedRoute handles the loading gate for protected pages.
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
