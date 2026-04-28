export type Role = 'candidate' | 'hr' | 'interviewer' | 'admin' | 'superadmin';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  avatar?: string;
  organizationId?: string;
}

export type CandidateStatus =
  | 'applied'
  | 'eligible'
  | 'round1'
  | 'round2'
  | 'round3'
  | 'interviewed'
  | 'selected'
  | 'rejected';

export interface Candidate {
  id: string;
  name: string;
  email: string;
  college: string;
  branch: string;
  cgpa: number;
  status: CandidateStatus;
  resumeUrl?: string;
  scores: AssessmentScore[];
  proctoringFlags: ProctoringFlag[];
  interviewFeedback?: InterviewFeedback;
  appliedAt: string;
}

export interface AssessmentScore {
  round: number;
  score: number;
  maxScore: number;
  completedAt: string;
}

export interface ProctoringFlag {
  id: string;
  type: 'tab_switch' | 'face_not_detected' | 'multiple_faces' | 'copy_paste';
  timestamp: string;
  details: string;
}

export interface InterviewFeedback {
  technicalScore: number;
  communicationScore: number;
  recommendation: 'select' | 'reject';
  notes: string;
  interviewerId: string;
  interviewerName: string;
  completedAt: string;
}

export type InterviewStatus = 'scheduled' | 'in_progress' | 'completed';

export interface InterviewAssignment {
  id: string;
  candidateId: string;
  candidate: Candidate;
  interviewerId: string;
  interviewerName?: string;
  round: string;
  status: InterviewStatus;
  scheduledAt: string;
  meetingLink?: string;
}

export interface AssignInterviewRequest {
  candidateId: string;
  interviewerId: string;
  scheduledAt: string;
  meetingLink: string;
  round?: string;
}

export interface InterviewFeedbackRequest {
  interviewId: string;
  candidateId: string;
  technicalScore: number;
  communicationScore: number;
  culturalFitScore: number;
  recommendation: 'select' | 'reject';
  notes: string;
}

export interface FinalDecisionRequest {
  decisions: Array<{
    candidateId: string;
    decision: 'selected' | 'rejected';
  }>;
}

export interface Assessment {
  id: string;
  candidateId: string;
  round: number;
  problems: Problem[];
  startedAt?: string;
  completedAt?: string;
  timeLimit: number;
  status: 'not_started' | 'in_progress' | 'completed';
}

export interface Problem {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  starterCode: string;
  testCases: TestCase[];
}

export interface TestCase {
  id: string;
  input: string;
  expectedOutput: string;
  isHidden: boolean;
}

export interface FunnelData {
  applied: number;
  eligible: number;
  assessed: number;
  interviewed: number;
  selected: number;
}

export interface AnalyticsData {
  passRatePerRound: { round: string; passRate: number }[];
  collegeBreakdown: { college: string; count: number; avgScore: number }[];
  branchPerformance: { branch: string; count: number; avgScore: number }[];
  proctoringViolations: { type: string; count: number }[];
}

export interface Organization {
  id: string;
  name: string;
  candidateCount: number;
  activeHiringCycles: number;
  plan: 'starter' | 'professional' | 'enterprise';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
