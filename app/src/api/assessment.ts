import { api } from './client';
import type { Assessment } from '../types';

export const assessmentApi = {
  start: (assessmentId: string) =>
    api.post<Assessment>(`/assessment/${assessmentId}/start`),

  submitSection: (assessmentId: string, data: { problemId: string; code: string }) =>
    api.post<{ passed: number; failed: number }>(`/assessment/${assessmentId}/submit-section`, data),

  getAssessment: (assessmentId: string) =>
    api.get<Assessment>(`/assessment/${assessmentId}`),

  getActiveAssessments: () =>
    api.get<Assessment[]>('/assessment/active'),

  submitFeedback: (candidateId: string, data: { technicalScore: number; communicationScore: number; recommendation: string; notes: string }) =>
    api.post(`/candidates/${candidateId}/feedback`, data),
};
