/**
 * Core types for the application
 * Matches backend models (without multi-tenant fields)
 *
 * All field names use snake_case to match the backend Pydantic serialization.
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
  email_verified?: boolean;
  resume_url?: string;
  govt_id_url?: string;
  scores: AssessmentScore[];
  proctoring_flags: ProctoringFlag[];
  interview_feedback?: InterviewFeedback;
  created_at: string;
  updated_at?: string;
  phone?: string;
  cycle_id?: string;
  passed_out_year: number;
  language_choice: string;
}

export interface AssessmentScore {
  round: string;
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
  recommendation: 'select' | 'reject' | 'hold';
  notes: string;
  interviewerId: string;
  interviewerName: string;
  completedAt: string;
}

export interface Assessment {
  id: string;
  candidate_id: string;
  round: string;
  status: string;
  questions_json: Record<string, unknown>;
  link_token: string;
  link_expiry: string;
  started_at?: string;
  ended_at?: string;
  time_limit: number;
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
  total_candidates: number;
  selected_count: number;
  select_rate: number;
  avg_cgpa: number;
  status_breakdown: Record<string, unknown>;
  pass_rate_per_round: { round: string; pass_rate: number }[];
  college_breakdown: { college: string; count: number; avg_score: number }[];
  branch_performance: { branch: string; count: number; avg_score: number }[];
  proctoring_violations: { type: string; count: number }[];
}

export interface Organization {
  id: string;
  name: string;
  candidate_count: number;
  active_hiring_cycles: number;
  plan: string;
}

export interface HiringCycle {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: 'active' | 'upcoming' | 'completed' | 'cancelled';
  eligibility_config: {
    min_cgpa: number;
    allowed_branches: string[];
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}
