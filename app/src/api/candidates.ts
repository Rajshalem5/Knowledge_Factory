/**
 * Candidates API client
 * Connects to /api/candidates endpoints
 */

import { api } from './client';
import type { Candidate, PaginatedResponse } from '../types';

export const candidatesApi = {
  /**
   * Get all candidates with pagination and filters
   * GET /api/candidates
   */
  getAll: (params?: { 
    page?: number; 
    pageSize?: number; 
    status?: string; 
    branch?: string; 
    college?: string; 
    search?: string 
  }) =>
    api.get<PaginatedResponse<Candidate>>('/api/candidates', { 
      params: params as Record<string, string | number> 
    }),

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
    
    // Use fetch for multipart/form-data
    const token = localStorage.getItem('kf_token');
    
    return fetch('/api/candidates/bulk-upload', {
      method: 'POST',
      headers: { 
        Authorization: `Bearer ${token}`,
        // Don't set Content-Type - let browser set it with boundary
      },
      body: formData,
    }).then(r => r.json());
  },

  /**
   * Preview bulk upload before saving
   * POST /api/candidates/bulk-upload/preview
   */
  previewBulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('kf_token');
    
    return fetch('/api/candidates/bulk-upload', {
      method: 'POST',
      headers: { 
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }).then(r => r.json());
  },
};
