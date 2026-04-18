import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assessmentApi } from '../api/assessment';

export function useAssessment(id: string) {
  return useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentApi.getAssessment(id),
    enabled: !!id,
  });
}

export function useActiveAssessments() {
  return useQuery({
    queryKey: ['assessments-active'],
    queryFn: assessmentApi.getActiveAssessments,
  });
}

export function useStartAssessment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assessmentApi.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments-active'] });
    },
  });
}

export function useSubmitSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ assessmentId, data }: { assessmentId: string; data: Parameters<typeof assessmentApi.submitSection>[1] }) =>
      assessmentApi.submitSection(assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment'] });
    },
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ candidateId, data }: { candidateId: string; data: Parameters<typeof assessmentApi.submitFeedback>[1] }) =>
      assessmentApi.submitFeedback(candidateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}
