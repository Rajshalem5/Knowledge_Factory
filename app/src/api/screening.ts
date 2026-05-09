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
  run: (params?: { branch?: string; college?: string; passed_out_year?: number; min_cgpa_override?: number }) =>
    api.post<ScreeningResult>('/api/screening/run', undefined, { params: params as Record<string, string | number> }),

  /**
   * Get pipeline stage stats with optional filters
   * GET /api/screening/pipeline-stats
   */
  getPipelineStats: (params?: { branch?: string; college?: string }) =>
    api.get<PipelineStats>('/api/screening/pipeline-stats', { params: params as Record<string, string | number> }),
};
