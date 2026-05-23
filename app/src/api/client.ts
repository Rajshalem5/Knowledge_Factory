/**
 * API Client - connects frontend to backend REST API
 * Access token in memory, refresh token in httpOnly cookie.
 * Auto-refreshes on 401 via cookie-based /refresh endpoint.
 */

import { tokenStore } from './token';

const API_BASE = import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== ''
  ? import.meta.env.VITE_API_URL
  : '';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

// Guard to prevent infinite 401 → refresh → 401 → refresh loop
let _isRefreshing = false;

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

  let response = await fetch(url, { ...fetchOptions, headers, credentials: 'include' });

  // 401 — if we had a token, try silent refresh via cookie, then retry once
  // _isRefreshing flag prevents infinite loop if /refresh itself returns 401
  // Skip refresh if there's no token (e.g. login with wrong password)
  if (response.status === 401 && !_isRefreshing && token) {
    _isRefreshing = true;
    try {
      // Call refresh directly (not through api.post) to bypass our own 401 handler
      const refreshRes = await fetch(
        `${API_BASE}/api/auth/refresh`,
        { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' } }
      );
      if (!refreshRes.ok) throw new Error('Refresh failed');
      const data = await refreshRes.json();
      const normalized = {
        token: data.access_token,
        refresh_token: data.refresh_token || '',
        user: {
          id: String(data.user.id),
          email: data.user.email,
          name: data.user.name,
          role: data.user.role.toLowerCase(),
        },
      };
      tokenStore.setAccessToken(normalized.token);

      headers['Authorization'] = `Bearer ${normalized.token}`;
      response = await fetch(url, { ...fetchOptions, headers, credentials: 'include' });
    } catch {
      tokenStore.clear();
      throw new Error('Session expired. Please log in again.');
    } finally {
      _isRefreshing = false;
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

  // Handle file downloads/blobs
  const acceptHeader = (fetchOptions.headers as Record<string, string>)?.['Accept'] || '';
  if (acceptHeader.includes('application/pdf') || contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
    return response.blob() as unknown as T;
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
