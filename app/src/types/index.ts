/**
 * Core types for the application
 * Matches backend models (without multi-tenant fields)
 */

export type Role = 'candidate' | 'hr' | 'admin' | 'superadmin' | 'interviewer';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
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
  email: string;
  name: string;
  college: string;
  branch: string;
  cgpa: number;
  status: string;
  display_status: string;
  resumeUrl?: string;
  govtIdUrl?: string;
  scores: AssessmentScore[];
  proctoringFlags: ProctoringFlag[];
  interviewFeedback?: InterviewFeedback;
  appliedAt: string;
  phone?: string;
  passedOutYear: number;
  languageChoice: string;
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
  plan: string;
}

export interface HiringCycle {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  status: 'active' | 'upcoming' | 'completed' | 'cancelled';
  eligibilityConfig: {
    minCGPA: number;
    allowedBranches: string[];
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
