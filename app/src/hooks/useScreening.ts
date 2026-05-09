import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { screeningApi } from '../api/screening';

export function useRunScreening() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params?: Record<string, string | number | boolean>) =>
      screeningApi.run(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-stats'] });
      queryClient.invalidateQueries({ queryKey: ['funnel'] });
    },
  });
}

export function usePipelineStats(params?: Record<string, string | number | boolean>) {
  return useQuery({
    queryKey: ['pipeline-stats', params],
    queryFn: () => screeningApi.getPipelineStats(params),
  });
}
