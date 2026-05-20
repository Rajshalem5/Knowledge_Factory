import { api } from '../api/client';

export interface ProctoringSessionResponse {
  session_id: string;
  ws_url: string;
  token: string;
  expires_at: string;
}

export const proctoringService = {
  initializeSession: async (assessment_attempt_id: string): Promise<ProctoringSessionResponse> => {
    try {
      const response = await api.post<any>('/api/proctoring/session', { assessment_attempt_id });
      console.log('Proctoring session response:', response);

      // Normalize response to handle potential variations (e.g., id vs session_id, camelCase vs snake_case)
      const data = response.data || response;
      const session_id = data.session_id || data.id || '';
      const ws_url = data.ws_url || data.wsUrl || '';
      const token = data.token || '';
      const expires_at = data.expires_at || data.expiresAt || '';

      if (!session_id) {
        console.error('Proctoring session initialization failed: missing session_id in response', data);
        throw new Error('Invalid proctoring session response');
      }

      return {
        session_id,
        ws_url,
        token,
        expires_at,
      };
    } catch (error) {
      console.error('Proctoring session initialization error:', error);
      throw error;
    }
  },

  recordEvent: (data: any) =>
    api.post('/api/proctoring/webhook/event', data), // Used by AI service but also could be used for frontend-only events

  terminateSession: (session_id: string, reason: string) =>
    api.post(`/api/proctoring/terminate/${session_id}`, { reason }),
};
