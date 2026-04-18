import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useFunnelData(organizationId?: string) {
  return useQuery({
    queryKey: ['funnel', organizationId],
    queryFn: () => analyticsApi.getFunnel(organizationId),
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
