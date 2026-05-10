import { useQuery } from '@tanstack/react-query';
import { analyticsApi, type FunnelFilters } from '../api/analytics';

export function useFunnelData(filters?: FunnelFilters) {
  return useQuery({
    queryKey: ['funnel', filters],
    queryFn: () => analyticsApi.getFunnel(filters),
  });
}

export function useAnalytics(organizationId?: string) {
  return useQuery({
    queryKey: ['analytics', organizationId],
    queryFn: () => analyticsApi.getAnalytics(organizationId),
  });
}

export function useOrganizations() {
  return useQuery({
    queryKey: ['organizations'],
    queryFn: analyticsApi.getOrganizations,
  });
}
