import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Badge, ProgressPipeline, LoadingState, ErrorState, Button } from '../../components/ui';
import { useMyCandidateProfile } from '../../hooks/useCandidates';
import { useActiveAssessments, useStartAssessment } from '../../hooks/useAssessment';
import { STATUS_LABELS } from '../../utils/roles';
import { Clock, FileText, Trophy, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { CandidateStatus, Assessment } from '../../types';

const PIPELINE_STEPS = [
  { id: 'applied', label: 'Applied' },
  { id: 'eligible', label: 'Eligible' },
  { id: 'round1', label: 'Round 1' },
  { id: 'round2', label: 'Round 2' },
  { id: 'round3', label: 'Round 3' },
  { id: 'interview', label: 'Interview' },
];

const STATUS_INDEX: Record<CandidateStatus, number> = {
  applied: 0,
  eligible: 1,
  round1: 2,
  round2: 3,
  round3: 4,
  interviewed: 5,
  selected: 6,
  rejected: 5,
};

export default function Portal() {
  const navigate = useNavigate();
  const { data: profile, isLoading: profileLoading, error: profileError } = useMyCandidateProfile();
  const { data: assessments } = useActiveAssessments();
  const startAssessment = useStartAssessment();

  const handleStartAssessment = () => {
    // Determine which round to start based on actual backend status
    let round = 'ROUND_2';
    if (profile?.status === 'ROUND2_PASSED') {
      round = 'ROUND_3';
    } else if (profile?.display_status === 'round2' || profile?.status === 'ROUND3_PASSED') {
      round = 'ROUND_3';
    } else if (profile?.display_status === 'round1' && profile?.status !== 'ROUND2_IN_PROGRESS') {
      round = 'ROUND_3';
    }
    startAssessment.mutate({ round }, {
      onSuccess: () => navigate('/assessment'),
    });
  };

  if (profileLoading) return <AppShell title="My Portal"><LoadingState /></AppShell>;
  if (profileError) return <AppShell title="My Portal"><ErrorState message="Failed to load profile" /></AppShell>;
  if (!profile) return <AppShell title="My Portal"><ErrorState message="Profile not found" /></AppShell>;

  const currentStep = STATUS_INDEX[profile.display_status as CandidateStatus] ?? 0;
  const isSelected = profile.display_status === 'selected';
  const isRejected = profile.display_status === 'rejected';

  return (
    <AppShell title="My Portal">
      <div className="max-w-4xl space-y-6">
        {/* Profile */}
        <Card>
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-on-surface tracking-tight-display">{profile.name}</h2>
              <p className="text-sm text-tertiary">{profile.email}</p>
            </div>
            <Badge
              variant={isSelected ? 'success' : isRejected ? 'danger' : 'warning'}
            >
              {STATUS_LABELS[profile.display_status as CandidateStatus] || profile.status}
            </Badge>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-tertiary uppercase tracking-architectural text-xs">College</span>
              <p className="font-medium text-on-surface">{profile.college}</p>
            </div>
            <div>
              <span className="text-tertiary uppercase tracking-architectural text-xs">Branch</span>
              <p className="font-medium text-on-surface">{profile.branch}</p>
            </div>
            <div>
              <span className="text-tertiary uppercase tracking-architectural text-xs">CGPA</span>
              <p className="font-medium text-on-surface">{profile.cgpa}</p>
            </div>
          </div>
        </Card>

        {/* Progress Pipeline */}
        <Card>
          <CardHeader>
            <CardTitle>Application Progress</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto py-2">
            <ProgressPipeline steps={PIPELINE_STEPS} currentStep={currentStep} />
          </div>
          {(isSelected || isRejected) && (
            <div className={`mt-4 p-3 rounded-md text-sm font-medium ${isSelected ? 'bg-secondary/10 text-secondary' : 'bg-danger/10 text-danger'}`}>
              {isSelected ? 'Congratulations! You have been selected.' : 'Your application was not selected this time.'}
            </div>
          )}
        </Card>

        {/* Active Assessments */}
        {assessments && assessments.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Active Assessments</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {assessments.map((a: Assessment) => (
                <div key={a.id} className="flex items-center justify-between p-3 rounded-md bg-[var(--bg-layer1)]">
                  <div className="flex items-center gap-3">
                    <FileText size={18} className="text-secondary" />
                    <div>
                      <p className="text-sm font-medium text-on-surface">
                        Round {a.round === 'ROUND_2' ? '2' : '3'} Assessment
                      </p>
                      <p className="text-xs text-tertiary">
                        <Clock size={10} className="inline mr-1" />
                        {a.time_limit} minutes
                      </p>
                    </div>
                  </div>
                  <Badge variant={a.status === 'IN_PROGRESS' ? 'warning' : 'default'}>
                    {a.status === 'IN_PROGRESS' ? 'In Progress' : a.status === 'COMPLETED' ? 'Completed' : 'Not Started'}
                  </Badge>
                  {a.status !== 'COMPLETED' && (
                    <button
                      onClick={() => navigate('/assessment')}
                      className="ml-3 text-secondary hover:text-secondary/80 transition-colors"
                    >
                      <ArrowRight size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Past Scores */}
        {profile.scores.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Past Results</CardTitle>
            </CardHeader>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {profile.scores.map(score => (
                <div key={score.round} className="p-3 rounded-md bg-[var(--bg-layer1)] text-center">
                  <Trophy size={18} className="mx-auto text-secondary mb-1" />
                  <p className="text-xs text-tertiary uppercase tracking-architectural">Round {score.round}</p>
                  <p className="text-lg font-bold text-on-surface">
                    {score.score}<span className="text-tertiary text-sm">/{score.maxScore}</span>
                  </p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Next Step */}
        {!isSelected && !isRejected && (
          <div className="p-4 rounded-md bg-secondary/5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary font-medium">Next Step</p>
                <p className="text-xs text-on-surface-variant mt-1">
                  {profile.display_status === 'applied' && 'Your application is being reviewed for eligibility.'}
                  {profile.display_status === 'eligible' && 'You are eligible! Start your assessment now.'}
                  {profile.status === 'ROUND2_PASSED' && 'You passed Round 1! Start Round 2 assessment.'}
                  {profile.status === 'ROUND3_PASSED' && 'You passed the assessments! Awaiting interview scheduling by HR.'}
                  {(profile.display_status === 'round1' && profile.status !== 'ROUND2_PASSED') && 'Your Round 1 assessment is in progress. Continue coding.'}
                  {(profile.display_status === 'round2' && profile.status !== 'ROUND3_PASSED') && 'Your Round 2 assessment is in progress. Continue working.'}
                  {profile.display_status === 'round3' && 'Your application is in the final round.'}
                  {profile.display_status === 'interviewed' && 'Interview complete. Results will be announced soon.'}
                </p>
              </div>
              {profile.display_status === 'eligible' && (
                <Button size="sm" onClick={handleStartAssessment} disabled={startAssessment.isPending}>
                  {startAssessment.isPending ? 'Starting...' : 'Start Assessment'}
                </Button>
              )}
              {/* Show button for next rounds after completing previous assessment */}
              {profile.status === 'ROUND2_PASSED' && (
                <Button size="sm" onClick={handleStartAssessment} disabled={startAssessment.isPending}>
                  {startAssessment.isPending ? 'Starting...' : 'Start Next Assessment'}
                </Button>
              )}
            </div>
            {startAssessment.isError && (
              <p className="text-xs text-danger mt-2">
                Failed to start assessment: {(startAssessment.error as Error)?.message || 'Unknown error'}
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
