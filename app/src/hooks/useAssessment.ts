import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assessmentApi } from '../api/assessment';
import type { AssessmentStartRequest, SubmissionCreateRequest } from '../api/assessment';

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
    mutationFn: (data: AssessmentStartRequest) => assessmentApi.start(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments-active'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-me'] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-stats'] });
      queryClient.invalidateQueries({ queryKey: ['funnel'] });
    },
  });
}

export function useSubmitSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SubmissionCreateRequest) => assessmentApi.submitSection(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-me'] });
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

export function useCompleteAssessment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assessmentId: string) => assessmentApi.complete(assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments-active'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-me'] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline-stats'] });
      queryClient.invalidateQueries({ queryKey: ['funnel'] });
    },
  });
}
