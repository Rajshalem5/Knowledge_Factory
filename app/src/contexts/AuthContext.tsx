import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User, Role } from '../types';
import { authApi } from '../api/auth';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, resume?: File) => Promise<void>;
  logout: () => void;
  role: Role | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function inferDevRole(email: string): Role {
  const normalized = email.toLowerCase();
  if (normalized.includes('interviewer')) return 'interviewer';
  if (normalized.includes('admin')) return 'admin';
  if (normalized.includes('superadmin')) return 'superadmin';
  if (normalized.includes('hr')) return 'hr';
  return 'candidate';
}

function createDevUser(email: string): User {
  const role = inferDevRole(email);
  return {
    id: `dev-${role}-1`,
    email,
    name: role === 'interviewer' ? 'Test Interviewer' : `Test ${role}`,
    role,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('kf_user');
    if (stored) return JSON.parse(stored);
    if (import.meta.env.DEV) {
      const demoUser = createDevUser('admin@example.com');
      localStorage.setItem('kf_user', JSON.stringify(demoUser));
      localStorage.setItem('kf_token', 'dev-token');
      return demoUser;
    }
    return null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('kf_token') || (import.meta.env.DEV ? 'dev-token' : null));
  const [isLoading, setIsLoading] = useState(false);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      let response;
      try {
        response = await authApi.login({ email, password });
      } catch (error) {
        if (!import.meta.env.DEV) throw error;
        response = {
          token: 'dev-token',
          user: createDevUser(email),
        };
      }
      localStorage.setItem('kf_token', response.token);
      localStorage.setItem('kf_user', JSON.stringify(response.user));
      setToken(response.token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string, resume?: File) => {
    setIsLoading(true);
    try {
      const response = await authApi.register({ name, email, password, resume });
      localStorage.setItem('kf_token', response.token);
      localStorage.setItem('kf_user', JSON.stringify(response.user));
      setToken(response.token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('kf_token');
    localStorage.removeItem('kf_user');
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, role: user?.role ?? null }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
