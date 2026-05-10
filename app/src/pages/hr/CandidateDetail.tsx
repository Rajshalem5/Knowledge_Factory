import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, AlertTriangle, Trophy } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Badge, Button, Tabs, LoadingState, ErrorState } from '../../components/ui';
import { useCandidate, useUpdateCandidateStatus } from '../../hooks/useCandidates';
import { STATUS_LABELS } from '../../utils/roles';
import type { CandidateStatus } from '../../types';

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: candidate, isLoading, error } = useCandidate(id!);
  const updateStatus = useUpdateCandidateStatus();

  if (isLoading) return <AppShell title="Candidate"><LoadingState /></AppShell>;
  if (error || !candidate) return <AppShell title="Candidate"><ErrorState message="Candidate not found" /></AppShell>;

  const handleStatusChange = (status: string) => {
    if (id) updateStatus.mutate({ id, status });
  };

  return (
    <AppShell title={candidate.name}>
      <div className="max-w-4xl space-y-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-sm text-tertiary hover:text-on-surface transition-colors"
        >
          <ArrowLeft size={14} />
          Back
        </button>

        <Card>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center">
                <span className="text-lg font-bold text-secondary">{candidate.name.charAt(0)}</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-on-surface tracking-tight-display">{candidate.name}</h2>
                <p className="text-sm text-tertiary">{candidate.email}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-tertiary">
                  <span>{candidate.college}</span>
                  <span className="text-[var(--border-ghost)]">|</span>
                  <span>{candidate.branch}</span>
                  <span className="text-[var(--border-ghost)]">|</span>
                  <span>CGPA: {candidate.cgpa}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={candidate.display_status === 'selected' ? 'success' : candidate.display_status === 'rejected' ? 'danger' : 'warning'}>
                {STATUS_LABELS[candidate.display_status as CandidateStatus] || candidate.status}
              </Badge>
              <Button variant="danger" size="sm" onClick={() => handleStatusChange('rejected')}>
                Reject
              </Button>
              <Button size="sm" onClick={() => handleStatusChange('selected')}>
                Select
              </Button>
            </div>
          </div>
        </Card>

        <Tabs
          tabs={[
            {
              id: 'scores',
              label: 'Scores',
              content: (
                <div className="space-y-3">
                  {candidate.scores.length === 0 ? (
                    <p className="text-sm text-tertiary">No scores yet.</p>
                  ) : (
                    candidate.scores.map(score => (
                      <div key={score.round} className="flex items-center justify-between p-3 rounded-md bg-[var(--bg-layer1)]">
                        <div className="flex items-center gap-3">
                          <Trophy size={16} className="text-secondary" />
                          <span className="text-sm font-medium text-on-surface">Round {score.round}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-on-surface">{score.score}</span>
                          <span className="text-tertiary text-sm">/{score.maxScore}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              ),
            },
            {
              id: 'proctoring',
              label: 'Proctoring',
              content: (
                <div className="space-y-2">
                  {(!candidate.proctoring_flags || candidate.proctoring_flags.length === 0) ? (
                    <p className="text-sm text-tertiary">No flags recorded.</p>
                  ) : (
                    candidate.proctoring_flags.map(flag => (
                      <div key={flag.id} className="flex items-center gap-3 p-3 rounded-md bg-danger/5">
                        <AlertTriangle size={14} className="text-danger" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-on-surface">{flag.type.replace(/_/g, ' ')}</p>
                          <p className="text-xs text-tertiary">{flag.details}</p>
                        </div>
                        <span className="text-xs text-tertiary">
                          {new Date(flag.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              ),
            },
            {
              id: 'interview',
              label: 'Interview',
              content: candidate.interview_feedback ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-md bg-[var(--bg-layer1)] text-center">
                      <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Technical</p>
                      <p className="text-2xl font-bold text-on-surface">
                        {candidate.interview_feedback.technicalScore}
                        <span className="text-sm text-tertiary">/10</span>
                      </p>
                    </div>
                    <div className="p-3 rounded-md bg-[var(--bg-layer1)] text-center">
                      <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Communication</p>
                      <p className="text-2xl font-bold text-on-surface">
                        {candidate.interview_feedback.communicationScore}
                        <span className="text-sm text-tertiary">/10</span>
                      </p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Notes</p>
                    <p className="text-sm text-on-surface-variant">{candidate.interview_feedback.notes}</p>
                  </div>
                  <Badge variant={candidate.interview_feedback.recommendation === 'select' ? 'success' : 'danger'}>
                    Recommended: {candidate.interview_feedback.recommendation === 'select' ? 'Select' : 'Reject'}
                  </Badge>
                </div>
              ) : (
                <p className="text-sm text-tertiary">No interview feedback yet.</p>
              ),
            },
            {
              id: 'resume',
              label: 'Resume',
              content: candidate.resume_url ? (
                <div className="flex items-center gap-3 p-4 rounded-md bg-[var(--bg-layer1)]">
                  <FileText size={20} className="text-secondary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-on-surface">Resume</p>
                    <p className="text-xs text-tertiary">Uploaded document</p>
                  </div>
                  <Button variant="secondary" size="sm">View</Button>
                </div>
              ) : (
                <p className="text-sm text-tertiary">No resume uploaded.</p>
              ),
            },
          ]}
        />
      </div>
    </AppShell>
  );
}
