/**
 * Interview API client
 * Connects to /api/candidates/:id/feedback endpoints
 */

import { api } from './client';

export interface FeedbackSubmitData {
  technicalScore: number;
  communicationScore: number;
  recommendation: string;
  notes: string;
}

export interface FeedbackResponse {
  id: string;
  technical: number;
  communication: number;
  recommendation: string;
  comments: string | null;
  submitted_at: string;
  interviewer_name: string | null;
}

export const interviewApi = {
  /**
   * Submit interview feedback for a candidate
   * POST /api/candidates/:candidateId/feedback
   */
  submitFeedback: (candidateId: string, data: FeedbackSubmitData) =>
    api.post<{ id: string; message: string }>(`/api/candidates/${candidateId}/feedback`, data),

  /**
   * Get interview feedback for a candidate
   * GET /api/candidates/:candidateId/feedback
   */
  getFeedback: (candidateId: string) =>
    api.get<FeedbackResponse[]>(`/api/candidates/${candidateId}/feedback`),
};
