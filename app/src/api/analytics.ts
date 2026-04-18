import { api } from './client';
import type { FunnelData, AnalyticsData, Organization } from '../types';

export const analyticsApi = {
  getFunnel: (organizationId?: string) =>
    api.get<FunnelData>('/analytics/funnel', { params: organizationId ? { organizationId } : undefined }),

  getAnalytics: (organizationId?: string) =>
    api.get<AnalyticsData>('/analytics/dashboard', { params: organizationId ? { organizationId } : undefined }),

  getOrganizations: () =>
    api.get<Organization[]>('/superadmin/organizations'),

  updateOrganization: (id: string, data: Partial<Organization>) =>
    api.patch<Organization>(`/superadmin/organizations/${id}`, data),
};
