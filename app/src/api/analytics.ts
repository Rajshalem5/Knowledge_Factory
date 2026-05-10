import { api } from './client';
import type { FunnelData, AnalyticsData, Organization } from '../types';

export interface FunnelFilters {
  branch?: string;
  college?: string;
  search?: string;
}

export const analyticsApi = {
  getFunnel: (filters?: FunnelFilters) =>
    api.get<FunnelData>('/api/analytics/funnel', { params: filters as Record<string, string | undefined> }),

  getAnalytics: (organizationId?: string) =>
    api.get<AnalyticsData>('/api/analytics/dashboard', { params: organizationId ? { organizationId } : undefined }),

  getOrganizations: () =>
    api.get<Organization[]>('/api/admin/organizations'),

  updateOrganization: (id: string, data: Partial<Organization>) =>
    api.patch<Organization>(`/api/admin/organizations/${id}`, data),
};
