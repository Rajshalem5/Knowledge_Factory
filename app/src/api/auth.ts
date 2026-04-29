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

export const authApi = {
  /**
   * Login with email and password
   * POST /api/auth/login
   */
  login: (data: LoginData) =>
    api.post<AuthResponse>('/api/auth/login', data),

  /**
   * Register new candidate or admin
   * POST /api/auth/register
   */
  register: (data: RegisterData) =>
    api.post<AuthResponse>('/api/auth/register', data),

  /**
   * Refresh access token using refresh token
   * POST /api/auth/refresh
   */
  refreshToken: (refreshToken: string) =>
    api.post<AuthResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    }),

  /**
   * Verify OTP code
   * POST /api/auth/verify-otp
   */
  verifyOtp: (data: { email: string; otp: string }) =>
    api.post<AuthResponse>('/api/auth/verify-otp', data),

  /**
   * Request password reset
   * POST /api/auth/forgot-password
   */
  forgotPassword: (data: { email: string }) =>
    api.post<{ message: string }>('/api/auth/forgot-password', data),

  /**
   * Reset password with token
   * POST /api/auth/reset-password
   */
  resetPassword: (data: { 
    token: string;
    new_password: string;
    confirm_password: string;
  }) =>
    api.post<{ message: string }>('/api/auth/reset-password', data),

  /**
   * Get current authenticated user
   * GET /api/auth/me
   */
  getMe: () =>
    api.get<{ 
      id: string;
      email: string;
      name: string;
      role: string;
    }>('/api/auth/me'),

  /**
   * Logout - notifies server to invalidate token
   * POST /api/auth/logout
   */
  logout: () =>
    api.post<null>('/api/auth/logout'),
};
