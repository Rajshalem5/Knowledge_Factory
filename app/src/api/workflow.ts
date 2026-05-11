/**
 * Workflow API - handles hiring process workflows
 */

import { api } from './client';

export interface ScreeningResult {
  screened: number;
  passed: number;
  rejected: number;
}

export interface QuestionGenerationRequest {
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  num_public_cases: number;
  num_private_cases: number;
}

export interface QuestionResponse {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  boilerplate: Record<string, string>;
  public_test_cases: Array<{
    input: string;
    expected_output: string;
  }>;
}

export interface Phase2StartResponse {
  message: string;
  assessment_id: string;
  questions_assigned: number;
  questions: Array<{
    id: string;
    title: string;
    difficulty: string;
  }>;
}

export const workflowApi = {
  // Round 1 Screening
  runScreening: () =>
    api.post<ScreeningResult>('/screening/run'),

  // Question Generation
  generateQuestion: (data: QuestionGenerationRequest) =>
    api.post<QuestionResponse>('/questions/generate', data),

  // Phase 2 Management
  startPhase2: (applicantId: string) =>
    api.post<Phase2StartResponse>(`/phase2/start/${applicantId}`),

  // Status Updates
  updateCandidateStatus: (candidateId: string, status: string) =>
    api.patch(`/candidates/${candidateId}/status`, { status }),

  // Get status transitions
  getStatusTransitions: () =>
    api.get<{
      transitions: Record<string, string[]>;
      description: string;
    }>('/candidates/status-transitions'),
};