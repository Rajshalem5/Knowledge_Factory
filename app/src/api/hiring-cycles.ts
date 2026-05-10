/**
 * Hiring Cycles API client
 * Connects to /api/hiring-cycles endpoints
 */

import { api } from './client';

export interface HiringCycleItem {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  eligibility_config: Record<string, unknown>;
  assessment_config: Record<string, unknown>;
  proctoring_config: Record<string, unknown>;
  created_at: string;
}

export const hiringCyclesApi = {
  getAll: () =>
    api.get<HiringCycleItem[]>('/api/hiring-cycles/'),
};
