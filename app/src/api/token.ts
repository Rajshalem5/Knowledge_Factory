/**
 * In-memory token storage.
 * Access token lives in module closure (not localStorage) to reduce XSS exposure.
 * Refresh token in localStorage as practical compromise until httpOnly cookies.
 */

let accessToken: string | null = null;

const REFRESH_KEY = 'kf_refresh_token';

export const tokenStore = {
  setAccessToken(token: string) {
    accessToken = token;
  },

  getAccessToken(): string | null {
    return accessToken;
  },

  setRefreshToken(token: string) {
    localStorage.setItem(REFRESH_KEY, token);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },

  clear() {
    accessToken = null;
    localStorage.removeItem(REFRESH_KEY);
  },
};
