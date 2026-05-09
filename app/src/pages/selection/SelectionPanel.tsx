import { useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Button, Toggle, LoadingState, ErrorState } from '../../components/ui';
import { useCandidates, useUpdateCandidateStatus } from '../../hooks/useCandidates';
import { CheckCircle, XCircle, Trophy } from 'lucide-react';

export default function SelectionPanel() {
  const { data: candidatesData, isLoading, error } = useCandidates({ limit: 100 });
  const updateStatus = useUpdateCandidateStatus();
  const [selections, setSelections] = useState<Record<string, boolean>>({});

  const candidates = (candidatesData?.data ?? []).filter(
    c => c.status === 'interviewed' || c.status === 'selected' || c.status === 'rejected'
  );

  const handleToggle = (id: string, selected: boolean) => {
    setSelections(prev => ({ ...prev, [id]: selected }));
  };

  const handleConfirmAll = () => {
    Object.entries(selections).forEach(([id, selected]) => {
      updateStatus.mutate({ id, status: selected ? 'selected' : 'rejected' });
    });
  };

  if (isLoading) return <AppShell title="Selection"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Selection"><ErrorState /></AppShell>;

  return (
    <AppShell title="Final Selection">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-on-surface tracking-tight-display">Final Selection</h2>
            <p className="text-sm text-tertiary">{candidates.length} candidates ready for final decision</p>
          </div>
          <Button onClick={handleConfirmAll} isLoading={updateStatus.isPending}>
            Confirm All Decisions
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {candidates.map(candidate => {
            const isSelected = selections[candidate.id] ?? candidate.status === 'selected';
            return (
              <Card key={candidate.id}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-secondary/20 flex items-center justify-center">
                      <span className="text-sm font-bold text-secondary">{candidate.name.charAt(0)}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-on-surface">{candidate.name}</p>
                      <p className="text-xs text-tertiary">{candidate.college}</p>
                    </div>
                  </div>
                  <Toggle
                    enabled={isSelected}
                    onChange={(val) => handleToggle(candidate.id, val)}
                  />
                </div>

                <div className="flex items-center gap-2 text-xs text-tertiary mb-3">
                  <span>{candidate.branch}</span>
                  <span>|</span>
                  <span>CGPA: {candidate.cgpa}</span>
                </div>

                {candidate.scores.length > 0 && (
                  <div className="flex gap-2 mb-3">
                    {candidate.scores.map(s => (
                      <span key={s.round} className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-layer1)] font-mono text-on-surface-variant">
                        R{s.round}: {s.score}/{s.maxScore}
                      </span>
                    ))}
                  </div>
                )}

                <div className={`flex items-center gap-1.5 pt-3 bg-[var(--bg-layer1)] -mx-4 -mb-4 px-4 pb-4 rounded-b-md text-xs font-medium ${
                  isSelected ? 'text-secondary' : 'text-danger'
                }`}>
                  {isSelected ? <CheckCircle size={12} /> : <XCircle size={12} />}
                  {isSelected ? 'Select' : 'Reject'}
                </div>
              </Card>
            );
          })}
        </div>

        {candidates.length === 0 && (
          <Card>
            <div className="py-12 text-center">
              <Trophy size={32} className="mx-auto mb-3 text-tertiary opacity-30" />
              <p className="text-sm text-tertiary">No candidates ready for selection</p>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
