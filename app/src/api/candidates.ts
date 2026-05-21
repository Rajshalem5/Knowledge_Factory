/**
 * Candidates API client
 * Connects to /api/candidates endpoints
 */

import { api } from './client';
import type { Candidate, PaginatedResponse, BulkUploadPreview } from '../types';

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

  /**
   * Get candidate by ID
   * GET /api/candidates/:id
   */
  getById: (id: string) =>
    api.get<Candidate>(`/api/candidates/${id}`),

  /**
   * Get current user's profile
   * GET /api/candidates/me
   */
  getMe: () =>
    api.get<Candidate>('/api/candidates/me'),

  /**
   * Update candidate status
   * PATCH /api/candidates/:id/status
   */
  updateStatus: (id: string, status: string) =>
    api.patch<Candidate>(`/api/candidates/${id}/status`, { status }),

  /**
   * Bulk upload candidates from CSV
   * POST /api/candidates/bulk-upload
   */
  bulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ batch_id: string; total_records: number; saved: number; errors: any[] }>('/api/candidates/bulk-upload', formData);
  },

  /**
   * Preview bulk upload before saving
   * POST /api/candidates/bulk-upload/preview
   */
  previewBulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<BulkUploadPreview>('/api/candidates/bulk-upload/preview', formData);
  },
};
