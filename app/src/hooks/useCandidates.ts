import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidatesApi } from '../api/candidates';

export function useCandidates(params?: Parameters<typeof candidatesApi.getAll>[0]) {
  return useQuery({
    queryKey: ['candidates', params],
    queryFn: () => candidatesApi.getAll(params),
  });
}

export function useCandidate(id: string) {
  return useQuery({
    queryKey: ['candidate', id],
    queryFn: () => candidatesApi.getById(id),
    enabled: !!id,
  });
}

export function useMyCandidateProfile() {
  return useQuery({
    queryKey: ['candidate-me'],
    queryFn: candidatesApi.getMe,
  });
}

export function useUpdateCandidateStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      candidatesApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-me'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-stats'] });
      queryClient.invalidateQueries({ queryKey: ['funnel'] });
    },
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => candidatesApi.uploadResume(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-me'] });
    },
  });
}

export function useBulkUpload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { file: File, data?: any }) => candidatesApi.bulkUpload(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-stats'] });
      queryClient.invalidateQueries({ queryKey: ['funnel'] });
    },
  });
}

export function usePreviewBulkUpload() {
  return useMutation({
    mutationFn: (file: File) => candidatesApi.previewBulkUpload(file),
  });
}
