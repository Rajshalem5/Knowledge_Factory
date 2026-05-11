/**
 * Authentication API client
 * Connects to /api/auth endpoints
 * Refresh token is stored as httpOnly cookie — not returned in response body.
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
  college: string;
  branch: string;
  cgpa: number;
  passed_out_year: number;
  language_choice: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string; // optional — now in httpOnly cookie
  token_type: 'bearer';
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

export interface NormalizedAuthResponse {
  token: string;
  refresh_token: string;
  user: User;
}

// Normalize role to lowercase for frontend
function normalizeResponse(res: AuthResponse): NormalizedAuthResponse {
  return {
    token: res.access_token,
    refresh_token: res.refresh_token || '', // cookie handles refresh
    user: {
      id: String(res.user.id),
      email: res.user.email,
      name: res.user.name,
      role: res.user.role.toLowerCase() as User['role'],
    },
  };
}

async function normalizeTokenResponse(res: AuthResponse): Promise<NormalizedAuthResponse> {
  return normalizeResponse(res);
}

export const authApi = {
  login: (data: LoginData) =>
    api.post<AuthResponse>('/api/auth/login', data).then(normalizeResponse),

  register: (data: RegisterData) =>
    api.post<AuthResponse>('/api/auth/register', data).then(normalizeResponse),

  refreshToken: () =>
    api.post<AuthResponse>('/api/auth/refresh'),

  verifyOtp: (data: { email: string; otp: string }) =>
    api.post<AuthResponse>('/api/auth/verify-otp', data).then(normalizeResponse),

  forgotPassword: (data: { email: string }) =>
    api.post<{ message: string }>('/api/auth/forgot-password', data),

  resetPassword: (data: { token: string; new_password: string; confirm_password: string }) =>
    api.post<{ message: string }>('/api/auth/reset-password', data),

  getMe: () =>
    api.get<{ id: string; email: string; name: string; role: string }>('/api/auth/me'),

  logout: () =>
    api.post<{ message: string }>('/api/auth/logout'),

  normalizeTokenResponse,
};
