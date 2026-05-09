import { useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Badge, Button, LoadingState, ErrorState } from '../../components/ui';
import { useCandidates } from '../../hooks/useCandidates';
import { useSubmitFeedback } from '../../hooks/useAssessment';
import { MessageSquare, Star } from 'lucide-react';

export default function InterviewPanel() {
  const { data: candidatesData, isLoading, error } = useCandidates({ status: 'interviewed', limit: 50 });
  const submitFeedback = useSubmitFeedback();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [technicalScore, setTechnicalScore] = useState('5');
  const [communicationScore, setCommunicationScore] = useState('5');
  const [recommendation, setRecommendation] = useState('select');
  const [notes, setNotes] = useState('');

  const candidates = candidatesData?.data ?? [];
  const selectedCandidate = candidates.find(c => c.id === selectedId);

  const handleSubmitFeedback = () => {
    if (!selectedId) return;
    submitFeedback.mutate({
      candidateId: selectedId,
      data: {
        technicalScore: parseInt(technicalScore),
        communicationScore: parseInt(communicationScore),
        recommendation,
        notes,
      },
    });
  };

  if (isLoading) return <AppShell title="Interview Panel"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Interview Panel"><ErrorState message="Failed to load candidates" /></AppShell>;

  return (
    <AppShell title="Interview Panel">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidate List */}
        <Card padding="none" className="lg:col-span-1">
          <div className="p-4 bg-[var(--bg-layer1)]">
            <CardTitle>Assigned Candidates</CardTitle>
          </div>
          <div className="divide-y divide-[var(--bg-layer1)]">
            {candidates.map(candidate => (
              <button
                key={candidate.id}
                onClick={() => setSelectedId(candidate.id)}
                className={`w-full text-left px-4 py-3 hover:bg-[var(--bg-layer1)] transition-colors ${
                  selectedId === candidate.id ? 'bg-secondary/5 border-l-2 border-secondary' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-on-surface">{candidate.name}</p>
                    <p className="text-xs text-tertiary">{candidate.college}</p>
                  </div>
                  <Badge variant="default">{candidate.branch}</Badge>
                </div>
              </button>
            ))}
            {candidates.length === 0 && (
              <div className="p-6 text-center text-sm text-tertiary">No candidates assigned</div>
            )}
          </div>
        </Card>

        {/* Feedback Form */}
        <div className="lg:col-span-2 space-y-4">
          {selectedCandidate ? (
            <>
              <Card>
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                    <span className="font-bold text-secondary">{selectedCandidate.name.charAt(0)}</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-on-surface tracking-tight-display">{selectedCandidate.name}</h3>
                    <p className="text-xs text-tertiary">
                      {selectedCandidate.college} | {selectedCandidate.branch} | CGPA: {selectedCandidate.cgpa}
                    </p>
                  </div>
                </div>
                {selectedCandidate.scores.length > 0 && (
                  <div className="mt-4 flex gap-3">
                    {selectedCandidate.scores.map(s => (
                      <div key={s.round} className="px-3 py-2 rounded-md bg-[var(--bg-layer1)] text-center">
                        <p className="text-[10px] text-tertiary uppercase tracking-architectural">Round {s.round}</p>
                        <p className="font-bold text-sm text-on-surface">{s.score}/{s.maxScore}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Interview Feedback</CardTitle>
                </CardHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="flex items-center gap-1 text-sm font-medium text-on-surface-variant">
                        <Star size={12} /> Technical Score
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min="0"
                          max="10"
                          value={technicalScore}
                          onChange={e => setTechnicalScore(e.target.value)}
                          className="flex-1 accent-secondary"
                        />
                        <span className="font-bold text-lg w-8 text-center text-on-surface">{technicalScore}</span>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <label className="flex items-center gap-1 text-sm font-medium text-on-surface-variant">
                        <MessageSquare size={12} /> Communication Score
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min="0"
                          max="10"
                          value={communicationScore}
                          onChange={e => setCommunicationScore(e.target.value)}
                          className="flex-1 accent-secondary"
                        />
                        <span className="font-bold text-lg w-8 text-center text-on-surface">{communicationScore}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-on-surface-variant">Recommendation</label>
                    <div className="flex gap-3">
                      <button
                        onClick={() => setRecommendation('select')}
                        className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                          recommendation === 'select'
                            ? 'bg-secondary/10 text-secondary'
                            : 'bg-[var(--bg-layer1)] text-tertiary'
                        }`}
                      >
                        Select
                      </button>
                      <button
                        onClick={() => setRecommendation('reject')}
                        className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                          recommendation === 'reject'
                            ? 'bg-danger/10 text-danger'
                            : 'bg-[var(--bg-layer1)] text-tertiary'
                        }`}
                      >
                        Reject
                      </button>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-on-surface-variant">Notes</label>
                    <textarea
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      rows={4}
                      placeholder="Write your interview notes..."
                      className="w-full rounded-md bg-[var(--bg-base)] px-3 py-2 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50"
                    />
                  </div>

                  <Button
                    className="w-full"
                    onClick={handleSubmitFeedback}
                    isLoading={submitFeedback.isPending}
                  >
                    Submit Feedback
                  </Button>
                </div>
              </Card>
            </>
          ) : (
            <Card>
              <div className="py-12 text-center text-tertiary">
                <MessageSquare size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a candidate to provide feedback</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </AppShell>
  );
}
