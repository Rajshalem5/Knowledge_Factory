import { useQuery } from '@tanstack/react-query';
import { analyticsApi, type FunnelFilters } from '../api/analytics';

export function useFunnelData(filters?: FunnelFilters) {
  return useQuery({
    queryKey: ['funnel', filters],
    queryFn: () => analyticsApi.getFunnel(filters),
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: analyticsApi.getAnalytics,
  });
}
