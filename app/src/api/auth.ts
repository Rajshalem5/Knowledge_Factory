/**
 * Authentication API client
 * Connects to /api/auth endpoints
 */

import { api } from './client';
import type { User } from '../types';

interface LoginData {
  email: string;
  password: string;
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

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

// Normalize role to lowercase for frontend
function normalizeResponse(res: AuthResponse): { token: string; user: User } {
  return {
    token: res.access_token,
    user: {
      id: String(res.user.id),
      email: res.user.email,
      name: res.user.name,
      role: res.user.role.toLowerCase() as User['role'],
    },
  };
}

export const authApi = {
  login: (data: LoginData) =>
    api.post<AuthResponse>('/auth/login', data).then(normalizeResponse),

  register: (data: RegisterData | FormData) =>
    api.post<AuthResponse>('/auth/register', data).then(normalizeResponse),

  refreshToken: (refreshToken: string) =>
    api.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }),

  verifyOtp: (data: { email: string; otp: string }) =>
    api.post<AuthResponse>('/auth/verify-otp', data).then(normalizeResponse),

  forgotPassword: (data: { email: string }) =>
    api.post<{ message: string }>('/auth/forgot-password', data),

  resetPassword: (data: { token: string; new_password: string; confirm_password: string }) =>
    api.post<{ message: string }>('/auth/reset-password', data),

  getMe: () =>
    api.get<{ id: string; email: string; name: string; role: string }>('/auth/me'),

  logout: () =>
    api.post<null>('/auth/logout'),
};
