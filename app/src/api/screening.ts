/**
 * Screening API client
 * Connects to /api/screening endpoints
 */

import { api } from './client';

export interface ScreeningResult {
  screened: number;
  passed: number;
  rejected: number;
  min_cgpa: number;
  allowed_branches: string[];
}

export interface PipelineStats {
  stats: Record<string, number>;
}

export interface ScreeningFilters {
  branch?: string;
  college?: string;
  passed_out_year?: number;
  language_choice?: string;
  min_cgpa_override?: number;
  search?: string;
  name?: string;
  cgpa_min?: number;
  cgpa_max?: number;
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
}

export const screeningApi = {
  /**
   * Run screening with optional extra filters
   * POST /api/screening/run
   */
  run: (params?: Record<string, string | number | boolean>) =>
    api.post<ScreeningResult>('/api/screening/run', undefined, { params }),

  getPipelineStats: (params?: Record<string, string | number | boolean>) =>
    api.get<PipelineStats>('/api/screening/pipeline-stats', { params }),
};
