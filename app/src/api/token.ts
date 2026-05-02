/**
 * In-memory token storage.
 * Access token lives in module closure (not localStorage) to reduce XSS exposure.
 * Refresh token is stored as httpOnly cookie by the backend — never touched client-side.
 */

let accessToken: string | null = null;

export const tokenStore = {
  setAccessToken(token: string) {
    accessToken = token;
  },

  getAccessToken(): string | null {
    return accessToken;
  },

  clear() {
    accessToken = null;
  },
};
