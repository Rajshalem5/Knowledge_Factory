import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  FileText, 
  AlertTriangle, 
  Trophy, 
  ExternalLink, 
  ShieldCheck, 
  CheckCircle2,
  HelpCircle
} from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Badge, Button, Tabs, LoadingState, ErrorState } from '../../components/ui';
import { Link } from 'react-router-dom';
import { useCandidate, useMakeDecision } from '../../hooks/useCandidates';
import { useHiringCycles } from '../../hooks/useHiringCycles';
import { candidatesApi } from '../../api/candidates';
import { getStatusLabel } from '../../utils/roles';
import type { Candidate } from '../../types';

type EligibilityConfig = {
  allowed_degrees?: string[];
  allowed_branches?: string[];
  passed_out_years?: number[];
  required_skills?: string[];
};

type CompositeCandidateInput = {
  screening_score?: number | null;
  mcq_score?: number | null;
  coding_score?: number | null;
  risk_penalty?: number | null;
  recommendation?: string | null;
  scores?: Array<{
    round: string;
    score?: number | null;
  }> | null;
  cgpa?: number | null;
  degree?: string | null;
  branch?: string | null;
  passed_out_year?: number | null;
  skills?: string | null;
  cycle_id?: string | null;
  cycleId?: string | null;
};

type ScreeningBreakdown = {
  cgpaScore: number;
  degreeScore: number;
  branchScore: number;
  yearScore: number;
  skillsScore: number;
  total: number;
};

type CompositeScore = {
  composite: number;
  backendPenalty: number;
  adjusted: number;
  recommendation: string | null;
  screening: number;
  mcq: number;
  coding: number;
};

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    console.log(`[CandidateDetail] Mounted for candidateId: ${id}`);
  }, [id]);

  const { data: candidate, isLoading, error } = useCandidate(id!);
  const makeDecision = useMakeDecision();
  const { data: cycles } = useHiringCycles();

  const [decisionReason, setDecisionReason] = useState('');
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [targetStatus, setTargetStatus] = useState<string | null>(null);
  const [isViewingResume, setIsViewingResume] = useState(false);

  if (isLoading) return <AppShell title="Candidate"><LoadingState /></AppShell>;
  if (error || !candidate) {
    console.error(`[CandidateDetail] Load error for ID ${id}:`, error);
    return <AppShell title="Candidate"><ErrorState message={`Candidate not found (ID: ${id})`} /></AppShell>;
  }

  // Ensure candidate is properly typed
  const candidateData = candidate as Candidate;

  const handleViewResume = async () => {
    if (!candidate.id) return;
    try {
      setIsViewingResume(true);
      const blob = await candidatesApi.getResume(candidate.id);
      const url = URL.createObjectURL(blob);
      const isPdf = blob.type === 'application/pdf';
      
      if (isPdf) {
        window.open(url, '_blank');
      } else {
        const link = document.createElement('a');
        link.href = url;
        link.download = `Resume_${candidate.name.replace(/\s+/g, '_')}${blob.type.includes('word') ? '.docx' : '.pdf'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      console.error('[CandidateDetail] Failed to view resume:', err);
      alert('Failed to load resume document.');
    } finally {
      setIsViewingResume(false);
    }
  };

  const handleStatusChange = (status: string, reason?: string) => {
    if (id) {
      console.log(`[CandidateDetail] Making decision: candidateId=${id}, status=${status}, reason=${reason}`);
      makeDecision.mutate({ id, status, reason });
    }
  };

  const openDecision = (status: string) => {
    setTargetStatus(status);
    setShowDecisionModal(true);
  };

  const confirmDecision = () => {
    if (targetStatus) {
      handleStatusChange(targetStatus, decisionReason);
      setShowDecisionModal(false);
    }
  };

  // Recommendations mapping
  const REC_VARIANTS: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
    'STRONGLY_RECOMMENDED': 'success',
    'RECOMMENDED': 'success',
    'BORDERLINE': 'warning',
    'NOT_RECOMMENDED': 'danger'
  };

  const safeNumber = (v: unknown): number | null => 
    (typeof v === 'number' && !Number.isNaN(v)) ? v : null;

  const findCycleConfig = (cycleId?: string | null): EligibilityConfig => {
    if (!cycleId || !cycles || !Array.isArray(cycles)) return {};
    const found = (cycles as Array<{ id: string; eligibility_config?: EligibilityConfig }>).find((c) => c.id === cycleId);
    return found?.eligibility_config || {};
  };

  const computeScreeningBreakdown = (cand: CompositeCandidateInput): ScreeningBreakdown => {
    const cfg = findCycleConfig(cand.cycle_id ?? cand.cycleId);
    const cgpa = safeNumber(cand.cgpa) ?? 0;
    const cgpaScore = Math.min(40, (cgpa / 10.0) * 40.0);

    const allowed_degrees = cfg?.allowed_degrees || [];
    const degreeOk = !allowed_degrees.length || (cand.degree && allowed_degrees.map((d: string) => d.toLowerCase()).includes(String(cand.degree).toLowerCase()));
    const degreeScore = degreeOk ? 20 : 0;

    const allowed_branches = cfg?.allowed_branches || [];
    const branchOk = !allowed_branches.length || (cand.branch && allowed_branches.map((b: string) => b.toLowerCase()).includes(String(cand.branch).toLowerCase()));
    const branchScore = branchOk ? 20 : 0;

    const allowed_years = cfg?.passed_out_years || [];
    const yearOk = !allowed_years.length || (cand.passed_out_year && allowed_years.includes(cand.passed_out_year));
    const yearScore = yearOk ? 10 : 0;

    const required_skills = cfg?.required_skills || [];
    let skillsScore = 0;
    if (!required_skills.length) {
      skillsScore = 10;
    } else if (cand.skills) {
      const candSkills = String(cand.skills).toLowerCase();
      const matched = required_skills.filter((s: string) => candSkills.includes(s.toLowerCase())).length;
      skillsScore = (matched / required_skills.length) * 10.0;
    }

    const total = Math.min(100, Math.round((cgpaScore + degreeScore + branchScore + yearScore + skillsScore) * 100) / 100);
    return {
      cgpaScore: Math.round(cgpaScore * 100) / 100,
      degreeScore: Math.round(degreeScore * 100) / 100,
      branchScore: Math.round(branchScore * 100) / 100,
      yearScore: Math.round(yearScore * 100) / 100,
      skillsScore: Math.round(skillsScore * 100) / 100,
      total,
    };
  };

  const computeComposite = (
    cand: CompositeCandidateInput
  ): CompositeScore => {
    const w = {
      screening: 0.2,
      mcq: 0.3,
      coding: 0.5,
    };

    const screening =
      safeNumber(cand.screening_score) ??
      computeScreeningBreakdown(cand).total;

    const mcq =
      safeNumber(cand.mcq_score) ??
      ((cand.scores ?? []).find(
        s => String(s.round).includes('2')
      )?.score ?? 0);

    const coding =
      safeNumber(cand.coding_score) ??
      ((cand.scores ?? []).find(
        s => String(s.round).includes('3')
      )?.score ?? 0);

    const composite =
      Math.round(
        (
          screening * w.screening +
          mcq * w.mcq +
          coding * w.coding
        ) * 100
      ) / 100;

    const backendPenalty =
      safeNumber(cand.risk_penalty) ?? 0;

    const adjusted = Math.max(
      0,
      composite - backendPenalty
    );

    const recommendation =
      cand.recommendation ??
      (
        adjusted >= 85
          ? 'STRONGLY_RECOMMENDED'
          : adjusted >= 70
            ? 'RECOMMENDED'
            : adjusted >= 60
              ? 'BORDERLINE'
              : 'NOT_RECOMMENDED'
      );

    return {
      composite,
      backendPenalty,
      adjusted,
      recommendation,
      screening,
      mcq,
      coding,
    };
  };

  const compositeInput: CompositeCandidateInput = {
    screening_score: candidateData.screening_score ?? null,
    mcq_score: candidateData.mcq_score ?? null,
    coding_score: candidateData.coding_score ?? null,
    risk_penalty: candidateData.risk_penalty ?? null,
    recommendation: candidateData.recommendation ?? null,
    scores: candidateData.scores ?? [],
    cgpa: candidateData.cgpa ?? null,
    degree: candidateData.degree ?? null,
    branch: candidateData.branch ?? null,
    passed_out_year: candidateData.passed_out_year ?? null,
    skills: candidateData.skills ?? null,
    cycle_id: candidateData.cycle_id ?? null,
    cycleId: (candidateData as any).cycleId ?? null,
  };

  const breakdown: ScreeningBreakdown = computeScreeningBreakdown(compositeInput);
  const comp: CompositeScore = computeComposite(compositeInput);
  const recommendation = candidateData.recommendation ?? comp.recommendation ?? 'NOT_RECOMMENDED';
  const interviewFeedback = candidateData.interview_feedback;

  const formatTimestamp = (ts: any) => {
    if (!ts) return 'N/A';
    const date = new Date(ts);
    return isNaN(date.getTime()) ? 'N/A' : date.toLocaleString();
  };

  const formatTime = (ts: any) => {
    if (!ts) return 'N/A';
    const date = new Date(ts);
    return isNaN(date.getTime()) ? 'N/A' : date.toLocaleTimeString();
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
                <span className="text-lg font-bold text-secondary">{candidateData.name.charAt(0)}</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-on-surface tracking-tight-display">{candidateData.name}</h2>
                <p className="text-sm text-tertiary">{candidateData.email}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-tertiary">
                  <span>{candidateData.college}</span>
                  <span className="text-[var(--border-ghost)]">|</span>
                  <span>{candidateData.branch}</span>
                  <span className="text-[var(--border-ghost)]">|</span>
                  <span>CGPA: {candidateData.cgpa}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={
                candidateData.display_status === 'selected' ? 'success' : 
                candidateData.display_status === 'rejected' ? 'danger' : 
                'warning'
              }>
                {getStatusLabel(candidateData)}
              </Badge>
              <div className="flex gap-1 ml-2">
                <Button variant="danger" size="sm" onClick={() => openDecision('FINAL_REJECTED')}>
                  Reject
                </Button>
                <Button variant="secondary" size="sm" onClick={() => openDecision('ROUND1_REVIEW')}>
                   Waitlist
                </Button>
                <Button size="sm" onClick={() => openDecision('SELECTED')}>
                  Select
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <Tabs
          tabs={[
            {
              id: 'evaluation',
              label: 'Evaluation Summary',
              content: (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="flex flex-col items-center justify-center p-6 text-center space-y-2 border-2 border-secondary/30 bg-secondary/5">
                      <Trophy size={24} className="text-secondary mb-1" />
                      <p className="text-[10px] text-tertiary uppercase font-bold tracking-widest">Final Adjusted Score</p>
                      <p className="text-5xl font-black text-on-surface">{candidateData.adjusted_final_score?.toFixed(1) || comp.adjusted.toFixed(1)}%</p>
                      <div className="pt-2 border-t border-secondary/20 w-full mt-2">
                         <p className="text-[10px] text-tertiary uppercase font-medium">Composite: {candidateData.composite_score?.toFixed(1) || comp.composite.toFixed(1)}%</p>
                         {(candidateData.risk_penalty ?? 0) > 0 && (
                            <p className="text-[10px] text-danger font-bold mt-1 flex items-center justify-center gap-1">
                               <AlertTriangle size={10} />
                               Risk Penalty: -{candidateData.risk_penalty}
                            </p>
                         )}
                      </div>
                    </Card>

                    <Card className="col-span-3 p-4 bg-[var(--bg-layer1)] rounded-md border border-ghost">
                      <div className="flex items-center justify-between mb-4">
                         <h4 className="text-sm font-bold text-on-surface uppercase tracking-architectural">Detailed Score Metrics</h4>
                         <Badge variant="info" className="text-[10px]">VERIFIED</Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <AnalysisField label="Screening" value={`${(candidateData.screening_score ?? comp.screening).toFixed(1)}%`} />
                        <AnalysisField label="MCQ (R2)" value={`${(candidateData.mcq_score ?? comp.mcq).toFixed(1)}%`} />
                        <AnalysisField label="Coding (R3)" value={`${(candidateData.coding_score ?? comp.coding).toFixed(1)}%`} />
                        <AnalysisField label="Composite" value={`${(candidateData.composite_score ?? comp.composite).toFixed(1)}%`} />
                      </div>

                      <div className="mt-6 pt-4 border-t border-ghost">
                         <h5 className="text-[10px] font-bold text-tertiary uppercase tracking-widest mb-3">Screening Breakdown (20% Weight)</h5>
                         <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                            <ScorePill label="CGPA" value={breakdown.cgpaScore} max={40} />
                            <ScorePill label="Degree" value={breakdown.degreeScore} max={20} />
                            <ScorePill label="Branch" value={breakdown.branchScore} max={20} />
                            <ScorePill label="Batch" value={breakdown.yearScore} max={10} />
                            <ScorePill label="Skills" value={breakdown.skillsScore} max={10} />
                         </div>
                      </div>

                      <div className="mt-6 pt-4 border-t border-ghost flex items-center justify-between bg-info/5 -mx-4 -mb-4 p-4">
                        <div>
                          <p className="text-[10px] text-info uppercase font-bold mb-1">AI Recommendation</p>
                          <Badge variant={REC_VARIANTS[recommendation] || 'default'}>
                             {recommendation.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <p className="text-[10px] text-tertiary max-w-[200px] text-right italic">
                          Generated based on adjusted final score and automated screening rules.
                        </p>
                      </div>
                    </Card>
                  </div>

                  {candidateData.decision_by && (
                    <Card className="bg-secondary/5 border-secondary/20">
                      <h4 className="text-xs font-bold text-secondary uppercase mb-2 flex items-center gap-2">
                        <ShieldCheck size={14} />
                        Manual Decision Override
                      </h4>
                      <p className="text-sm italic text-on-surface-variant mb-3">"{candidateData.decision_reason || 'No reason provided.'}"</p>
                      <div className="flex justify-between items-center text-[10px] text-tertiary">
                         <span>Decision by ID: {candidateData.decision_by}</span>
                         <span>{formatTimestamp(candidateData.decision_timestamp)}</span>
                      </div>
                    </Card>
                  )}
                </div>
              )
            },
            {
              id: 'scores',
              label: 'Scores',
              content: (
                <div className="space-y-3">
                  {candidateData.scores.length === 0 ? (
                    <p className="text-sm text-tertiary">No scores yet.</p>
                  ) : (
                    candidateData.scores.map((score, idx) => {
                      const assessmentId = candidateData.assessments?.find((a: any) => a.round === score.round)?.id;                    
                        return (
                        <div key={`${score.round}-${idx}`} className="flex items-center justify-between p-3 rounded-md bg-[var(--bg-layer1)] border border-ghost hover:border-secondary/30 transition-colors group">
                          <div className="flex items-center gap-3">
                            <Trophy size={16} className="text-secondary" />
                            <span className="text-sm font-medium text-on-surface">Round {score.round.replace(/_/g, ' ')}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <span className="font-bold text-on-surface">{score.score}</span>
                              <span className="text-tertiary text-sm">/{score.maxScore || 100}</span>
                            </div>
                            {assessmentId && (
                              <Link 
                                to={`/candidates/${id}/assessments/${assessmentId}`}
                                className="p-1.5 rounded bg-secondary/10 text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                                title="View Details"
                              >
                                <ExternalLink size={14} />
                              </Link>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              ),
            },
            {
              id: 'proctoring',
              label: 'Proctoring',
              content: (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="text-sm font-bold text-tertiary uppercase tracking-wider">Violation Summary</h4>
                    <Link 
                      to={`/candidates/${id}/proctoring`}
                      className="flex items-center gap-1.5 text-xs font-bold text-secondary hover:underline"
                    >
                      <ExternalLink size={12} />
                      View Full Audit Timeline
                    </Link>
                  </div>
                  <div className="space-y-2">
                  {(!candidateData.proctoring_flags || candidateData.proctoring_flags.length === 0) ? (
                    <p className="text-sm text-tertiary">No flags recorded.</p>
                  ) : (
                    candidateData.proctoring_flags.map((flag, idx) => (
                      <div key={`${flag.id}-${idx}`} className="flex items-center gap-3 p-3 rounded-md bg-danger/5">
                        <AlertTriangle size={14} className="text-danger" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-on-surface">{flag.type.replace(/_/g, ' ')}</p>
                          <p className="text-xs text-tertiary">{flag.details}</p>
                        </div>
                        <span className="text-xs text-tertiary">
                          {formatTime(flag.timestamp)}
                        </span>
                      </div>
                    ))
                  )}
                  </div>
                </div>
              ),
            },
            {
              id: 'analysis',
              label: 'Resume Analysis',
              content: (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-on-surface uppercase tracking-wider">AI Extraction Results</h3>
                      <p className="text-[10px] text-tertiary mt-1">Fields parsed from uploaded document</p>
                    </div>
                <div className="flex items-center gap-2">
                   {candidateData.resume_url && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={handleViewResume}
                        isLoading={isViewingResume}
                        className="text-[10px] uppercase font-bold text-secondary"
                      >
                         <FileText size={12} className="mr-1" />
                         View Original
                      </Button>
                   )}
                   <Badge variant="info">AI POWERED</Badge>
                </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    <AnalysisField label="Full Name" value={candidateData.name} />
                    <AnalysisField label="Email" value={candidateData.email} />
                    <AnalysisField label="Phone" value={candidateData.phone} />
                    <AnalysisField label="College / University" value={candidateData.college} />
                    <AnalysisField label="Degree" value={candidateData.degree} />
                    <AnalysisField label="Branch" value={candidateData.branch} />
                    <AnalysisField label="CGPA" value={candidateData.cgpa} />
                    <AnalysisField label="Graduation Year" value={candidateData.passed_out_year} />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-tertiary">Skills Detected</label>
                  <div className="flex flex-wrap gap-2">
                    {candidateData.skills && candidateData.skills.trim() ? candidateData.skills.split(',').filter(s => s.trim()).map((s: string, i: number) => (
                      <Badge key={i} variant="info">{s.trim()}</Badge>
                    )) : <span className="text-sm text-tertiary">No skills detected</span>}
                  </div>
                  </div>

                  {candidateData.custom_fields && Object.keys(candidateData.custom_fields).length > 0 && (
                    <div className="pt-4 border-t border-ghost space-y-3">
                       <h4 className="text-[10px] font-bold text-tertiary uppercase tracking-widest">Additional Extracted Info</h4>
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(candidateData.custom_fields).map(([k, v]) => (
                            v ? <AnalysisField key={k} label={k.replace(/_/g, ' ')} value={String(v)} /> : null
                          ))}
                       </div>
                    </div>
                  )}

                  <div className="p-4 bg-info/5 border border-info/20 rounded-lg">
                    <h4 className="text-xs font-bold text-info uppercase mb-2 flex items-center gap-2">
                      <HelpCircle size={14} />
                      Data Integrity Check
                    </h4>
                    <ul className="space-y-2">
                      {!candidate.phone && (
                        <li className="text-xs text-warning-on-container flex items-center gap-2">
                           <AlertTriangle size={12} className="text-warning" />
                           <span className="font-bold">Missing Field:</span> Phone number not found in resume.
                        </li>
                      )}
                      {(!candidate.skills || !candidate.skills.trim()) && (
                        <li className="text-xs text-warning-on-container flex items-center gap-2">
                           <AlertTriangle size={12} className="text-warning" />
                           <span className="font-bold">Missing Field:</span> Skills section could not be parsed.
                        </li>
                      )}
                      {candidate.cgpa === 0 && (
                        <li className="text-xs text-warning-on-container flex items-center gap-2">
                           <AlertTriangle size={12} className="text-warning" />
                           <span className="font-bold">Low Confidence:</span> CGPA is reported as 0.0. Manual verification required.
                        </li>
                      )}
                      {candidate.name && candidate.email && candidate.phone && candidate.college && candidate.skills && (
                         <li className="text-xs text-success flex items-center gap-2">
                            <CheckCircle2 size={12} />
                            All primary candidate identifiers successfully extracted.
                         </li>
                      )}
                    </ul>
                  </div>
                </div>
              )
            },
            {
              id: 'interview',
              label: 'Interview',
              content: interviewFeedback ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-md bg-[var(--bg-layer1)] text-center">
                      <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Technical</p>
                      <p className="text-2xl font-bold text-on-surface">
                        {interviewFeedback.technicalScore}
                        <span className="text-sm text-tertiary">/10</span>
                      </p>
                    </div>
                    <div className="p-3 rounded-md bg-[var(--bg-layer1)] text-center">
                      <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Communication</p>
                      <p className="text-2xl font-bold text-on-surface">
                        {interviewFeedback.communicationScore}
                        <span className="text-sm text-tertiary">/10</span>
                      </p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Notes</p>
                    <p className="text-sm text-on-surface-variant">{interviewFeedback.notes}</p>
                  </div>
                  <Badge variant={
                    interviewFeedback.recommendation === 'select' ? 'success' :
                    interviewFeedback.recommendation === 'hold' ? 'warning' : 'danger'
                  }>
                    Recommended: {interviewFeedback.recommendation === 'select' ? 'Select' :
                      interviewFeedback.recommendation === 'hold' ? 'Hold' : 'Reject'}
                  </Badge>
                </div>
              ) : (
                <p className="text-sm text-tertiary">No interview feedback yet.</p>
              ),
            },
            {
              id: 'resume',
              label: 'Resume',
              content: candidateData.resume_url ? (
                <div className="flex items-center gap-3 p-4 rounded-md bg-[var(--bg-layer1)]">
                  <FileText size={20} className="text-secondary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-on-surface">Resume Document</p>
                    <p className="text-xs text-tertiary">Stored as: {candidateData.resume_url.split('/').pop()}</p>
                  </div>
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    onClick={handleViewResume}
                    isLoading={isViewingResume}
                  >
                    View Document
                  </Button>
                </div>
              ) : (
                <p className="text-sm text-tertiary">No resume uploaded.</p>
              ),
            },
          ]}
        />
      </div>

      {/* Decision Modal */}
      {showDecisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4">
          <div className="bg-[var(--bg-base)] w-full max-w-md p-6 rounded-lg border border-outline-variant shadow-2xl space-y-4">
            <h2 className="text-xl font-bold text-on-surface flex items-center gap-2">
               <ShieldCheck className="text-secondary" />
               Confirm Hiring Decision
            </h2>
            <div className="text-sm text-on-surface-variant leading-relaxed">
              You are about to change the status of <strong>{candidateData.name}</strong> to 
              <Badge className="ml-1 uppercase">{targetStatus?.replace(/_/g, ' ')}</Badge>.
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-tertiary">Decision Reason / Notes</label>
              <textarea
                value={decisionReason}
                onChange={(e) => setDecisionReason(e.target.value)}
                placeholder="Provide a justification for this decision..."
                className="w-full h-32 p-3 bg-[var(--bg-layer1)] rounded-md border border-ghost text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button onClick={() => setShowDecisionModal(false)} variant="ghost">Cancel</Button>
              <Button onClick={confirmDecision} isLoading={makeDecision.isPending}>
                Confirm Decision
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function ScorePill({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div className="p-2 rounded bg-white/5 border border-ghost">
      <p className="text-[9px] text-tertiary uppercase mb-1">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className="font-bold text-sm">{value}</span>
        <span className="text-[10px] text-tertiary">/{max}</span>
      </div>
    </div>
  );
}

function AnalysisField({ label, value }: { label: string; value: string | number | undefined | null }) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] font-bold uppercase tracking-widest text-tertiary">{label}</p>
      <p className="text-sm font-medium text-on-surface">{value || <span className="text-danger italic text-[10px] uppercase">Not found</span>}</p>
    </div>
  );
}
