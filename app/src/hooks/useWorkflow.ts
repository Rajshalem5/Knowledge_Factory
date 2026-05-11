/**
 * Workflow hooks - React Query hooks for hiring workflow operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { workflowApi, type QuestionGenerationRequest } from '../api/workflow';

export function useRunScreening() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: workflowApi.runScreening,
    onSuccess: () => {
      // Invalidate candidates list to refresh status
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });
}

export function useGenerateQuestion() {
  return useMutation({
    mutationFn: (data: QuestionGenerationRequest) => workflowApi.generateQuestion(data),
  });
}

export function useStartPhase2() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (applicantId: string) => workflowApi.startPhase2(applicantId),
    onSuccess: () => {
      // Invalidate candidates list to refresh status
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

export function useUpdateCandidateStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ candidateId, status }: { candidateId: string; status: string }) =>
      workflowApi.updateCandidateStatus(candidateId, status),
    onSuccess: () => {
      // Invalidate candidates list to refresh status
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });
}

export function useStatusTransitions() {
  return useQuery({
    queryKey: ['status-transitions'],
    queryFn: workflowApi.getStatusTransitions,
  });
}