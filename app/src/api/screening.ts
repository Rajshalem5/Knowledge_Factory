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

export const screeningApi = {
  /**
   * Run screening with optional extra filters
   * POST /api/screening/run
   */
  run: (params?: Record<string, string | number>) =>
    api.post<ScreeningResult>('/api/screening/run', undefined, { params }),

  getPipelineStats: (params?: Record<string, string | number>) =>
    api.get<PipelineStats>('/api/screening/pipeline-stats', { params }),
};
