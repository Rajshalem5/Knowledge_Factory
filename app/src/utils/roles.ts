import type { Role, CandidateStatus } from '../types';

export const ROLE_LABELS: Record<Role, string> = {
  candidate: 'Candidate',
  hr: 'HR Recruiter',
  interviewer: 'Interviewer',
  admin: 'Admin',
  superadmin: 'Super Admin',
};

export const ROLE_HOME_ROUTES: Record<Role, string> = {
  candidate: '/portal',
  hr: '/dashboard',
  interviewer: '/interview',
  admin: '/dashboard',
  superadmin: '/superadmin',
};

/**
 * Prefer using getStatusLabel(candidate) over STATUS_LABELS directly,
 * since display_status may be undefined or mismatch the type.
 */
export const STATUS_LABELS: Record<CandidateStatus, string> = {
  applied: 'Applied',
  eligible: 'Eligible',
  round1: 'Round 1',
  round2: 'Round 2',
  round3: 'Round 3',
  interviewed: 'Interviewed',
  selected: 'Selected',
  rejected: 'Rejected',
};

export const STATUS_COLORS: Record<CandidateStatus, string> = {
  applied: 'bg-surface-variant/40 text-on-surface-variant',
  eligible: 'bg-info/15 text-info',
  round1: 'bg-secondary/15 text-secondary',
  round2: 'bg-secondary/20 text-secondary',
  round3: 'bg-secondary/25 text-secondary',
  interviewed: 'bg-info/15 text-info',
  selected: 'bg-secondary/10 text-secondary',
  rejected: 'bg-danger/15 text-danger',
};

/** Safely get the display label for a candidate's status. Falls back to raw status string. */
export function getStatusLabel(candidate: { display_status?: string; status?: string }): string {
  const display = candidate.display_status;
  if (display && display in STATUS_LABELS) {
    return STATUS_LABELS[display as CandidateStatus];
  }
  if (candidate.status) {
    return candidate.status;
  }
  return 'Unknown';
}

export function canAccessRoute(role: Role, route: string): boolean {
  const routes: Record<Role, string[]> = {
    candidate: ['/portal', '/assessment'],
    hr: ['/dashboard', '/candidates', '/selection', '/analytics'],
    interviewer: ['/interview', '/candidates'],
    admin: ['/dashboard', '/candidates', '/selection', '/analytics', '/interview'],
    superadmin: ['/superadmin', '/dashboard', '/candidates', '/selection', '/analytics'],
  };
  return routes[role]?.some(r => route.startsWith(r)) ?? false;
}
