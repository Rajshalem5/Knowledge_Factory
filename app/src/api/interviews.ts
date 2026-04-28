import { api } from './client';
import type {
  AssignInterviewRequest,
  Candidate,
  FinalDecisionRequest,
  InterviewAssignment,
  InterviewFeedbackRequest,
} from '../types';

export const interviewsApi = {
  assign: (data: AssignInterviewRequest) =>
    api.post<InterviewAssignment>('/interviews/assign', data),

  getMyAssignments: () =>
    api.get<InterviewAssignment[]>('/interviews/my-assignments'),

  submitFeedback: (data: InterviewFeedbackRequest) =>
    api.post('/interviews/feedback', data),

  getFinalReviewCandidates: () =>
    api.get<Candidate[]>('/candidates/final-review'),

  submitFinalDecision: (data: FinalDecisionRequest) =>
    api.post('/candidates/final-decision', data),
};
