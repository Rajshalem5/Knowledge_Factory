/**
 * Candidates API client
 * Connects to /api/candidates endpoints
 */

import { api } from './client';
import type { Candidate, PaginatedResponse } from '../types';

export interface AssessmentResult {
  assessment_id: string;
  round: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  time_limit: number;
  submissions: {
    id: string;
    section: string;
    submitted_at: string | null;
    code_snippet: string;
  }[];
  scores: {
    id: string;
    correctness: number;
    quality: number;
    design: number;
    weighted_total: number;
    verdict: string;
    evaluated_at: string | null;
  }[];
}

export const candidatesApi = {
  getAll: (params?: {
    page?: number;
    limit?: number;
    status?: string;
    name?: string;
    branch?: string;
    college?: string;
    search?: string;
    passed_out_year?: number;
    cgpa_min?: number;
    cgpa_max?: number;
    language_choice?: string;
    has_resume?: boolean;
    has_govt_id?: boolean;
    created_after?: string;
    created_before?: string;
    passed_out_year_min?: number;
    passed_out_year_max?: number;
    email_verified?: boolean;
    phone?: string;
    email?: string;
    cycle_id?: string;
    has_phone?: boolean;
    has_assessment?: boolean;
    has_interview_feedback?: boolean;
    updated_after?: string;
    updated_before?: string;
    assessment_status?: string;
    min_score?: number;
    max_score?: number;
    sort_by?: string;
    sort_order?: string;
  }) =>
    api.get<PaginatedResponse<Candidate>>('/api/candidates/', {
      params: params as Record<string, string | number | boolean | undefined>,
    }),

  getById: (id: string) =>
    api.get<Candidate>(`/api/candidates/${id}`),

  getMe: () =>
    api.get<Candidate>('/api/candidates/me'),

  updateStatus: (id: string, status: string) =>
    api.patch<Candidate>(`/api/candidates/${id}/status`, { status }),

  bulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<unknown>('/api/candidates/bulk-upload', formData) as Promise<unknown>;
  },

  previewBulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<unknown>('/api/candidates/bulk-upload/preview', formData) as Promise<unknown>;
  },

  getAssessments: (id: string) =>
    api.get<{ data: AssessmentResult[] }>(`/api/candidates/${id}/assessments`),
};
