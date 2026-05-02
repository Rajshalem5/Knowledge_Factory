/**
 * API Client - connects frontend to backend REST API
 * Access token in memory, refresh token in localStorage.
 * Auto-refreshes on 401.
 */

import { tokenStore } from './token';
import { authApi } from './auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${endpoint}`;

  if (params) {
    const entries = Object.entries(params).filter(([, v]) => v != null && v !== '');
    if (entries.length) {
      url += `?${new URLSearchParams(entries.map(([k, v]) => [k, String(v)]))}`;
    }
  }

  const token = tokenStore.getAccessToken();
  const isFormData = fetchOptions.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((fetchOptions.headers as Record<string, string>) || {}),
  };

  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  let response = await fetch(url, { ...fetchOptions, headers });

  // 401 — attempt silent refresh, then retry once
  if (response.status === 401) {
    const refreshToken = tokenStore.getRefreshToken();
    if (refreshToken) {
      try {
        const refreshRes = await authApi.refreshToken(refreshToken);
        const normalized = await authApi.normalizeTokenResponse(refreshRes);
        tokenStore.setAccessToken(normalized.token);
        tokenStore.setRefreshToken(refreshRes.refresh_token);

        headers['Authorization'] = `Bearer ${normalized.token}`;
        response = await fetch(url, { ...fetchOptions, headers });
      } catch {
        tokenStore.clear();
        throw new Error('Session expired. Please log in again.');
      }
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let message = `HTTP ${response.status}`;

    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map((err: Record<string, unknown>) => err.msg || JSON.stringify(err)).join(', ');
      } else {
        message = errorData.detail;
      }
    } else if (errorData.message) {
      message = errorData.message;
    }

    throw new Error(message);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }

  return {} as T;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined),
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined),
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined),
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};

export { API_BASE };
