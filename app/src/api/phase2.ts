/**
 * Phase 2 Assessment API client
 * HR triggers AI assessment, candidates take it
 */

import { api } from './client';

export interface Phase2StartResult {
  message: string;
  assessment_id: string;
  questions_assigned: number;
  questions: { id: string; title: string; difficulty: string }[];
}

export interface Phase2Result {
  candidate: { name: string; email: string };
  status: string;
  overall_score: number;
  overall_verdict: string;
  question_scores: {
    title: string;
    difficulty: string;
    language: string;
    score_percentage: number;
    marks_obtained: number;
    total_marks: number;
    verdict: string;
    submitted_at: string;
  }[];
}

export const phase2Api = {
  /** HR triggers Phase 2 for a shortlisted candidate */
  startForCandidate: (applicantId: string) =>
    api.post<Phase2StartResult>(`/phase2/start/${applicantId}`),

  /** HR views candidate's Phase 2 results */
  getResults: (applicantId: string) =>
    api.get<Phase2Result>(`/phase2/results/${applicantId}`),

  /** Candidate gets their assigned assessment */
  getMyAssessment: () =>
    api.get('/phase2/my-assessment'),

  /** Candidate submits code for a question */
  submitCode: (data: { question_id: string; language: string; code: string; time_spent?: number }) =>
    api.post('/phase2/submit', data),
};
