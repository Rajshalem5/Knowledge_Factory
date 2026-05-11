/**
 * Jobs / Hiring Cycles API client
 * Connects to /api/jobs endpoints
 */

import { api } from './client';

export interface Job {
  id: string;
  title: string;
  job_description: string;
  skillset: string[];
  location: string;
  experience_level: string;
  openings: number;
  status: string;
  created_at: string | null;
}

export const jobsApi = {
  getAll: () =>
    api.get<{ data: Job[] }>('/jobs/').then(response => response.data),

  create: (data: { 
    title: string; 
    job_description: string;
    skillset: string[];
    location?: string;
    experience_level?: string;
    openings?: number;
  }) =>
    api.post<Job>('/jobs/', data),

  update: (id: string, data: { title?: string; status?: string }) =>
    api.patch<{ message: string }>(`/jobs/${id}`, data),
};
