import { api } from './client';
import type { FunnelData, AnalyticsData, Organization } from '../types';

export interface FunnelFilters {
  branch?: string;
  college?: string;
  search?: string;
  name?: string;
  passed_out_year?: number;
  language_choice?: string;
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
  status?: string;
  has_phone?: boolean;
}

export const analyticsApi = {
  getFunnel: (filters?: FunnelFilters) =>
    api.get<FunnelData>('/api/analytics/funnel', { params: filters as Record<string, string | number | boolean | undefined> }),

  getAnalytics: (organizationId?: string) =>
    api.get<AnalyticsData>('/api/analytics/dashboard', { params: organizationId ? { organizationId } : undefined }),

  getOrganizations: () =>
    api.get<Organization[]>('/api/admin/organizations'),

  updateOrganization: (id: string, data: Partial<Organization>) =>
    api.patch<Organization>(`/api/admin/organizations/${id}`, data),
};
