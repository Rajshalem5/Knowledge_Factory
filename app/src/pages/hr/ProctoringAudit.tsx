import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Badge, LoadingState, ErrorState } from '../../components/ui';
import { useProctoringSession, useProctoringEvents, useProctoringEvidence } from '../../hooks/useProctoring';
import { useCandidate } from '../../hooks/useCandidates';
import { AlertTriangle, Clock, Camera, Shield, User, FileText } from 'lucide-react';

export default function ProctoringAudit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: candidate, isLoading: isCandidateLoading } = useCandidate(id!);
  
  // Find the latest active or completed assessment
  const latestAssessmentId = candidate?.assessments?.sort((a: any, b: any) => 
    new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime()
  )[0]?.id;

  const { data: session, isLoading: isSessionLoading, error: sessionError } = useProctoringSession(latestAssessmentId!);
  const { data: events, isLoading: isEventsLoading } = useProctoringEvents(session?.session_id);
  const { data: evidence, isLoading: isEvidenceLoading } = useProctoringEvidence(session?.session_id);

  if (isCandidateLoading || isSessionLoading) return <AppShell title="Proctoring Audit"><LoadingState /></AppShell>;
  
  if (sessionError || !session) return (
    <AppShell title="Proctoring Audit">
      <div className="space-y-6">
        <button onClick={() => navigate(-1)} className="text-sm text-tertiary hover:text-on-surface">&larr; Back</button>
        <ErrorState message="No proctoring session found for this candidate's latest assessment." />
      </div>
    </AppShell>
  );

  return (
    <AppShell title={`Proctoring Audit: ${candidate?.name}`}>
      <div className="max-w-6xl space-y-6">
        <div className="flex justify-between items-center">
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-tertiary hover:text-on-surface transition-colors">
            &larr; Back to Candidate
          </button>
          <div className="flex gap-2 text-xs text-tertiary">
            <span className="flex items-center gap-1"><Clock size={12} /> Started: {new Date(session.started_at).toLocaleString()}</span>
            {session.ended_at && <span className="flex items-center gap-1">Ended: {new Date(session.ended_at).toLocaleString()}</span>}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="md:col-span-1 space-y-6">
            <div>
              <h3 className="text-xs text-tertiary uppercase font-bold tracking-widest mb-4">Risk Profile</h3>
              <div className="flex flex-col items-center justify-center p-6 bg-[var(--bg-layer1)] rounded-full w-32 h-32 mx-auto border-4 border-ghost">
                <span className={`text-3xl font-black ${session.final_risk_score > 60 ? 'text-danger' : session.final_risk_score > 20 ? 'text-warning' : 'text-success'}`}>
                  {Math.round(session.final_risk_score)}
                </span>
                <span className="text-[10px] text-tertiary uppercase">Risk Score</span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-tertiary">Violations</span>
                <span className="font-bold">{session.total_violations}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-tertiary">Status</span>
                <Badge variant={session.status === 'TERMINATED' ? 'danger' : 'success'}>{session.status}</Badge>
              </div>
              {session.terminated_reason && (
                <div className="pt-2 border-t border-ghost">
                  <p className="text-[10px] text-tertiary uppercase mb-1">Termination Reason</p>
                  <p className="text-xs text-danger">{session.terminated_reason}</p>
                </div>
              )}
            </div>
          </Card>

          <div className="md:col-span-3 space-y-6">
            <Card>
              <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                <Shield size={20} className="text-secondary" />
                Evidence Timeline
              </h3>
              
              <div className="relative border-l-2 border-ghost ml-3 pl-8 space-y-8">
                {events?.length === 0 ? (
                  <p className="text-sm text-tertiary py-4 italic">No suspicious events recorded during this session.</p>
                ) : (
                  events?.map((evt: any, idx: number) => (
                    <div key={idx} className="relative">
                      <div className={`absolute -left-[41px] top-0 w-5 h-5 rounded-full border-4 border-[var(--bg-surface)] ${
                        evt.severity === 'HIGH' ? 'bg-danger' : evt.severity === 'MEDIUM' ? 'bg-warning' : 'bg-success'
                      }`} />
                      <div className="bg-[var(--bg-layer1)] p-4 rounded-md border border-ghost">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-bold text-sm uppercase tracking-tight">{evt.event_type.replace(/_/g, ' ')}</span>
                            <span className="ml-3 text-[10px] text-tertiary">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <Badge variant={evt.severity === 'HIGH' ? 'danger' : 'warning'} size="sm">
                            Score +{evt.risk_score}
                          </Badge>
                        </div>
                        <p className="text-xs text-on-surface-variant leading-relaxed">
                          {evt.metadata?.details || 'System detection alert.'}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {evidence && evidence.length > 0 && (
              <Card>
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Camera size={20} className="text-secondary" />
                  Visual Evidence
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {evidence.map((item: any, idx: number) => (
                    <div key={idx} className="space-y-2">
                      <div className="aspect-video bg-ghost rounded-md flex items-center justify-center border border-ghost overflow-hidden">
                        {item.screenshot_url ? (
                          <img src={item.screenshot_url} alt="Evidence" className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-[10px] text-tertiary">Image Ref: {item.id.slice(0,8)}</span>
                        )}
                      </div>
                      <div className="flex justify-between items-center px-1">
                        <span className="text-[10px] text-tertiary">{new Date(item.created_at).toLocaleTimeString()}</span>
                        <Badge size="sm">{item.event_type}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
