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
    api.post<Assessment>('/assessment/start', data),

  submitSection: (data: SubmissionCreateRequest) =>
    api.post<{ passed: number; failed: number }>('/assessment/submit-section', data),

  getAssessment: (assessmentId: string) =>
    api.get<Assessment>(`/assessment/${assessmentId}`),

  getActiveAssessments: () =>
    api.get<Assessment[]>('/assessment/active'),

  submitFeedback: (candidateId: string, data: { technicalScore: number; communicationScore: number; recommendation: string; notes: string }) =>
    api.post(`/candidates/${candidateId}/feedback`, data),
};
