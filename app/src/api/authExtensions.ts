/**
 * Auth API client extensions
 * /api/auth endpoints — confirm-password, delete-account
 */

import { api } from './client';

export const authExtensions = {
  confirmPassword: (password: string) =>
    api.post<{ verified: boolean; user_id: string }>('/api/auth/confirm-password', { password }),

  deleteAccount: (reauth_token: string) =>
    api.delete<{ message: string }>('/api/auth/delete-account', {
      body: JSON.stringify({ reauth_token }),
      headers: { 'Content-Type': 'application/json' },
    }),
};