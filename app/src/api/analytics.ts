import { api } from './client';
import type { FunnelData, AnalyticsData, Organization } from '../types';

export const analyticsApi = {
  getFunnel: (organizationId?: string) =>
    api.get<FunnelData>('/api/analytics/funnel', { params: organizationId ? { organizationId } : undefined }),

  getAnalytics: (organizationId?: string) =>
    api.get<AnalyticsData>('/api/analytics/dashboard', { params: organizationId ? { organizationId } : undefined }),

  getOrganizations: () =>
    api.get<Organization[]>('/api/admin/organizations'),

  updateOrganization: (id: string, data: Partial<Organization>) =>
    api.patch<Organization>(`/api/admin/organizations/${id}`, data),
};
