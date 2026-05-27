/**
 * Candidates API client
 * Connects to /api/candidates endpoints
 */

import { api } from './client';
import type { Candidate, PaginatedResponse, BulkUploadPreview, BulkUploadResponse } from '../types';

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
  /**
   * Get all candidates with pagination and filters
   * GET /api/candidates
   */
  getAll: async (params?: { 
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
  }) => {
    console.log('[candidatesApi] Fetching candidates with params:', params);
    const response = await api.get<any>('/api/candidates/', { 
      params: params as Record<string, string | number | boolean | undefined> 
    });
    console.log('[candidatesApi] Received response:', response);
    
    // Normalize response structure
    if (Array.isArray(response)) {
      return {
        data: response,
        pagination: {
          page: params?.page || 1,
          limit: params?.limit || response.length,
          total: response.length,
          total_pages: 1
        }
      };
    }
    
    return response as PaginatedResponse<Candidate>;
  },

  getById: (id: string) =>
    api.get<Candidate>(`/api/candidates/${id}`),

  getMe: () =>
    api.get<Candidate>('/api/candidates/me'),

  /**
   * Upload resume
   * POST /api/candidates/me/resume
   */
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ message: string; resume_url: string }>('/api/candidates/me/resume', formData);
  },

  /**
   * Update candidate status
   * PATCH /api/candidates/:id/status
   */
  updateStatus: (id: string, status: string) =>
    api.patch<Candidate>(`/api/candidates/${id}/status`, { status }),

  /**
   * Make a final hiring decision with reason
   * POST /api/selection/candidates/:id/decision
   */
  makeDecision: (id: string, status: string, reason?: string) =>
    api.post<any>(`/api/selection/candidates/${id}/decision`, { status, reason }),

  /**
   * Bulk upload candidates from CSV or documents
   * POST /api/candidates/bulk-upload
   */
  bulkUpload: (params: { file: File, data?: any, onDuplicate?: 'skip' | 'update' }) => {
    const formData = new FormData();
    formData.append('file', params.file);
    if (params.data) {
      formData.append('data', JSON.stringify(params.data));
    }
    const query = params.onDuplicate ? `?on_duplicate=${params.onDuplicate}` : '';
    return api.post<BulkUploadResponse>(`/api/candidates/bulk-upload${query}`, formData);
  },

  previewBulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<BulkUploadPreview>('/api/candidates/bulk-upload/preview', formData);
  },

  /**
   * Get resume file blob
   * GET /api/candidates/:id/resume
   */
  getResume: (id: string) =>
    api.get<Blob>(`/api/candidates/${id}/resume`, {
      headers: {
        'Accept': 'application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/msword'
      }
    }),
};
