import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { interviewsApi } from '../api/interviews';
import type { Candidate, InterviewAssignment } from '../types';

const demoCandidates: Candidate[] = [
  {
    id: 'demo-candidate-1',
    name: 'Marcus Aurelius',
    email: 'marcus@example.com',
    college: 'Knowledge Institute',
    branch: 'Senior UX Architect',
    cgpa: 8.7,
    status: 'interviewed',
    scores: [
      { round: 1, score: 85, maxScore: 100, completedAt: '2026-04-20' },
      { round: 2, score: 78, maxScore: 100, completedAt: '2026-04-22' },
    ],
    proctoringFlags: [],
    appliedAt: '2026-04-01',
  },
  {
    id: 'demo-candidate-2',
    name: 'Ada Lovelace',
    email: 'ada@example.com',
    college: 'Analytical College',
    branch: 'Algorithm Developer',
    cgpa: 9.1,
    status: 'interviewed',
    scores: [
      { round: 1, score: 92, maxScore: 100, completedAt: '2026-04-18' },
      { round: 2, score: 88, maxScore: 100, completedAt: '2026-04-21' },
    ],
    proctoringFlags: [],
    appliedAt: '2026-04-03',
  },
  {
    id: 'demo-candidate-3',
    name: 'Satya Nadella',
    email: 'satya@example.com',
    college: 'Cloud University',
    branch: 'Cloud Infrastructure Lead',
    cgpa: 8.9,
    status: 'selected',
    scores: [
      { round: 1, score: 89, maxScore: 100, completedAt: '2026-04-17' },
      { round: 2, score: 91, maxScore: 100, completedAt: '2026-04-19' },
    ],
    proctoringFlags: [],
    appliedAt: '2026-03-29',
  },
];

const demoAssignments: InterviewAssignment[] = [
  {
    id: 'demo-interview-1',
    candidateId: demoCandidates[0].id,
    candidate: demoCandidates[0],
    interviewerId: 'marcus',
    interviewerName: 'Marcus Lee',
    round: 'Technical Interview',
    status: 'scheduled',
    scheduledAt: '2026-04-29T14:00:00.000Z',
    meetingLink: 'https://meet.google.com/abc-defg-hij',
  },
  {
    id: 'demo-interview-2',
    candidateId: demoCandidates[1].id,
    candidate: demoCandidates[1],
    interviewerId: 'elena',
    interviewerName: 'Elena Rao',
    round: 'System Design',
    status: 'in_progress',
    scheduledAt: '2026-04-28T10:00:00.000Z',
    meetingLink: 'https://meet.google.com/system-design',
  },
  {
    id: 'demo-interview-3',
    candidateId: demoCandidates[2].id,
    candidate: demoCandidates[2],
    interviewerId: 'david',
    interviewerName: 'David Kim',
    round: 'Executive',
    status: 'completed',
    scheduledAt: '2026-04-24T09:30:00.000Z',
    meetingLink: 'https://meet.google.com/executive',
  },
];

async function withDevFallback<T>(request: () => Promise<T>, fallback: T) {
  try {
    const data = await request();
    if (import.meta.env.DEV && Array.isArray(data) && data.length === 0) {
      return fallback;
    }
    return data;
  } catch (error) {
    if (import.meta.env.DEV) return fallback;
    throw error;
  }
}

export function useMyInterviewAssignments() {
  return useQuery({
    queryKey: ['interviews', 'my-assignments'],
    queryFn: () => withDevFallback(interviewsApi.getMyAssignments, demoAssignments),
  });
}

export function useFinalReviewCandidates() {
  return useQuery({
    queryKey: ['candidates', 'final-review'],
    queryFn: () => withDevFallback(interviewsApi.getFinalReviewCandidates, demoCandidates),
  });
}

export function useAssignInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: interviewsApi.assign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['candidates', 'final-review'] });
    },
  });
}

export function useSubmitInterviewFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: interviewsApi.submitFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

export function useSubmitFinalDecision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: interviewsApi.submitFinalDecision,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates', 'final-review'] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}
