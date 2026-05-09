import { api } from './client';
import type { Assessment } from '../types';

export interface AssessmentStartRequest {
  round: string;
}

export interface SubmissionCreateRequest {
  assessment_id: string;
  section: string;
  content: { problemId?: string; code?: string };
  time_spent_seconds?: number;
}

export const assessmentApi = {
  start: (data: AssessmentStartRequest) =>
    api.post<Assessment>('/api/assessment/start', data),

  submitSection: (data: SubmissionCreateRequest) =>
    api.post<{ passed: number; failed: number }>('/api/assessment/submit-section', data),

  getAssessment: (assessmentId: string) =>
    api.get<Assessment>(`/api/assessment/${assessmentId}`),

  getActiveAssessments: () =>
    api.get<Assessment[]>('/api/assessment/active'),

  submitFeedback: (candidateId: string, data: { technicalScore: number; communicationScore: number; recommendation: string; notes: string }) =>
    api.post(`/api/candidates/${candidateId}/feedback`, data),

  complete: (assessmentId: string) =>
    api.post<Assessment>(`/api/assessment/${assessmentId}/complete`),
};
