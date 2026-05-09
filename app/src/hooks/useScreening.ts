import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { screeningApi } from '../api/screening';

export function useRunScreening() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params?: { branch?: string; college?: string; passed_out_year?: number; min_cgpa_override?: number }) =>
      screeningApi.run(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

export function usePipelineStats(params?: { branch?: string; college?: string }) {
  return useQuery({
    queryKey: ['pipeline-stats', params],
    queryFn: () => screeningApi.getPipelineStats(params),
  });
}
