import { AppShell } from '../../components/layout/AppShell';
import { Card, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { useCandidates } from '../../hooks/useCandidates';
import { Calculator, Trophy } from 'lucide-react';
import type { Candidate } from '../../types';

export default function SelectionPanel() {
  // Fetch candidates
  const { data: candidatesData, isLoading, error } = useCandidates({ 
    limit: 200, 
    sort_by: 'adjusted_final_score', 
    sort_order: 'desc' 
  });
  
  const rawCandidates = Array.isArray(candidatesData?.data) ? candidatesData.data : [];

  // Filter: Only show candidates who cleared all 3 rounds (Screening, MCQ, Coding)
  const qualifiedStatuses = ['ROUND3_PASSED', 'INTERVIEW_SCHEDULED', 'INTERVIEW_COMPLETED', 'SELECTED'];
  
  const candidates = rawCandidates
    .filter(c => qualifiedStatuses.includes(c.status))
    .sort((a, b) => {
      const scoreA = a.adjusted_final_score ?? a.composite_score ?? a.screening_score ?? 0;
      const scoreB = b.adjusted_final_score ?? b.composite_score ?? b.screening_score ?? 0;
      return scoreB - scoreA;
    });

  const columns: Column<Candidate>[] = [
    {
      key: 'rank',
      header: 'Rank',
      render: (_, idx) => <span className="font-black text-secondary">#{idx + 1}</span>
    },
    {
      key: 'name',
      header: 'Candidate',
      render: (c) => (
        <div>
          <p className="font-bold text-on-surface">{c.name}</p>
          <p className="text-[10px] text-tertiary">{c.college}</p>
        </div>
      )
    },
    {
      key: 'score',
      header: 'Score',
      render: (c) => {
        const score = c.adjusted_final_score ?? c.composite_score ?? 0;
        return (
          <div className="flex items-center gap-2">
             <Calculator size={12} className="text-tertiary" />
             <span className="font-mono font-bold text-sm">{score.toFixed(1)}%</span>
          </div>
        );
      }
    },
    {
      key: 'status',
      header: 'Stage',
      render: (c) => {
        const labels: Record<string, string> = {
          'ROUND3_PASSED': 'CODING PASSED',
          'INTERVIEW_SCHEDULED': 'INTERVIEWING',
          'INTERVIEW_COMPLETED': 'INTERVIEWED',
          'SELECTED': 'SELECTED',
          'FINAL_REJECTED': 'REJECTED'
        };
        const label = labels[c.status] || c.display_status?.toUpperCase() || 'QUALIFIED';
        return (
          <Badge variant={c.status === 'SELECTED' ? 'success' : c.status === 'FINAL_REJECTED' ? 'danger' : 'default'}>
            {label}
          </Badge>
        );
      }
    }
  ];

  if (isLoading) return <AppShell title="Selection"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Selection"><ErrorState /></AppShell>;

  return (
    <AppShell title="Ranking & Selection">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-on-surface">Final Selection Leaderboard</h1>
            <p className="text-sm text-tertiary">Ranking candidates who successfully cleared Screening, MCQ, and Coding rounds</p>
          </div>
          <Trophy size={32} className="text-secondary opacity-50" />
        </div>

        {candidates.length > 0 ? (
          <Card padding="none">
             <DataTable
               columns={columns}
               data={candidates}
               keyExtractor={c => c.id}
             />
          </Card>
        ) : (
          <Card>
            <div className="py-20 text-center space-y-4">
               <Trophy size={48} className="mx-auto text-ghost" />
               <p className="text-tertiary">No candidates have completed evaluations yet.</p>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
