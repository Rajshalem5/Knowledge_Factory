/**
 * API Client - connects frontend to backend REST API
 * Base URL from environment variable, JWT token auto-attached
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;
  
  // Build full URL with base + endpoint
  let url = `${API_BASE}${endpoint}`;
  
  // Add query params if provided
  if (params) {
    const queryString = new URLSearchParams(
      Object.entries(params).map(([key, value]) => [key, String(value)])
    ).toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  // Get stored token and attach to headers
  const token = localStorage.getItem('kf_token');
  const isFormData = fetchOptions.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((fetchOptions.headers as Record<string, string>) || {}),
  };

  // Only set application/json if not FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url.toString(), { 
    ...fetchOptions, 
    headers 
  });

  // Handle errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let message = `HTTP ${response.status}`;
    
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
      } else {
        message = errorData.detail;
      }
    } else if (errorData.message) {
      message = errorData.message;
    }
    
    throw new Error(message);
  }

  // Parse response body
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }

  // Return empty object for non-JSON responses (e.g., 204 No Content)
  return {} as T;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, data?: any, options?: RequestOptions) =>
    request<T>(endpoint, { 
      ...options, 
      method: 'POST', 
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined)
    }),

  put: <T>(endpoint: string, data?: any, options?: RequestOptions) =>
    request<T>(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined)
    }),

  patch: <T>(endpoint: string, data?: any, options?: RequestOptions) =>
    request<T>(endpoint, { 
      ...options, 
      method: 'PATCH', 
      body: data instanceof FormData ? data : (data ? JSON.stringify(data) : undefined)
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Export base URL for direct usage
export { API_BASE };
