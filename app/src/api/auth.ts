import { api } from './client';
import type { User } from '../types';

interface AuthResponse {
  token: string;
  user: User;
}

export const authApi = {
  register: (data: { name: string; email: string; password: string; resume?: File }) => {
    if (data.resume) {
      const formData = new FormData();
      formData.append('name', data.name);
      formData.append('email', data.email);
      formData.append('password', data.password);
      formData.append('resume', data.resume);
      return fetch('/api/auth/register', { method: 'POST', body: formData })
        .then(r => r.json() as Promise<AuthResponse>);
    }
    return api.post<AuthResponse>('/auth/register', data);
  },

  login: (data: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data),

  verifyOtp: (data: { email: string; otp: string }) =>
    api.post<AuthResponse>('/auth/verify-otp', data),

  forgotPassword: (data: { email: string }) =>
    api.post<{ message: string }>('/auth/forgot-password', data),

  resetPassword: (data: { token: string; password: string }) =>
    api.post<{ message: string }>('/auth/reset-password', data),

  getMe: () =>
    api.get<User>('/auth/me'),
};
