import { api } from './client';
import type { Candidate, PaginatedResponse } from '../types';

export const candidatesApi = {
  getAll: (params?: { page?: number; pageSize?: number; status?: string; branch?: string; college?: string; search?: string }) =>
    api.get<PaginatedResponse<Candidate>>('/candidates', { params: params as Record<string, string> }),

  getById: (id: string) =>
    api.get<Candidate>(`/candidates/${id}`),

  getMe: () =>
    api.get<Candidate>('/candidates/me'),

  updateStatus: (id: string, status: string) =>
    api.patch<Candidate>(`/candidates/${id}/status`, { status }),

  bulkUpload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch('/api/candidates/bulk-upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('kf_token')}` },
      body: formData,
    }).then(r => r.json());
  },
};
