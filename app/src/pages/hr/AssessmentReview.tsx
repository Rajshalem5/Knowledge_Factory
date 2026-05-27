// React import not needed in modern JSX transform
import { useParams, useNavigate } from 'react-router-dom';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Badge, LoadingState, ErrorState } from '../../components/ui';
import { useAssessmentAdmin } from '../../hooks/useAssessment';
import { useCandidate } from '../../hooks/useCandidates';
import { Trophy, Code, CheckCircle, XCircle } from 'lucide-react';

export default function AssessmentReview() {
  const { id, assessmentId } = useParams<{ id: string; assessmentId: string }>();
  const navigate = useNavigate();
  
  const { data: assessment, isLoading: isAssessmentLoading, error: assessmentError } = useAssessmentAdmin(assessmentId!);
  const { data: candidate, isLoading: isCandidateLoading } = useCandidate(id!);

  if (isAssessmentLoading || isCandidateLoading) return <AppShell title="Assessment Review"><LoadingState /></AppShell>;
  if (assessmentError || !assessment) return <AppShell title="Assessment Review"><ErrorState message="Failed to load assessment details" /></AppShell>;

  const codingSubmission = assessment.submissions?.find((s: any) => s.section === 'CODING');
  const mcqSubmission = assessment.submissions?.find((s: any) => s.section === 'MCQ');
  
  // Find the score for this round
  const score = candidate?.scores?.find((s: any) => s.round === assessment.round);

  return (
    <AppShell title={`Review: ${candidate?.name || 'Candidate'}`}>
      <div className="max-w-6xl space-y-6">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-tertiary hover:text-on-surface transition-colors">
          &larr; Back to Candidate
        </button>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-1 space-y-4">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Trophy size={18} className="text-secondary" />
              Summary
            </h3>
            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center border-b border-ghost pb-2">
                <span className="text-sm text-tertiary">Round</span>
                <Badge>{assessment.round.replace(/_/g, ' ')}</Badge>
              </div>
              <div className="flex justify-between items-center border-b border-ghost pb-2">
                <span className="text-sm text-tertiary">Status</span>
                <Badge variant={assessment.status === 'COMPLETED' ? 'success' : 'warning'}>
                  {assessment.status}
                </Badge>
              </div>
              {score && (
                <>
                  <div className="flex justify-between items-center border-b border-ghost pb-2">
                    <span className="text-sm text-tertiary">Verdict</span>
                    <Badge variant={(score as any).verdict === 'PASS' ? 'success' : 'danger'}>
                      {(score as any).verdict}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-tertiary">Score</span>
                    <span className="text-lg font-bold text-on-surface">{score.score}%</span>
                  </div>
                </>
              )}
            </div>
          </Card>

          <div className="md:col-span-2 space-y-6">
            {codingSubmission && (
              <Card className="space-y-4">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Code size={18} className="text-secondary" />
                  Coding Submission
                </h3>
                <div className="bg-[var(--bg-layer1)] p-4 rounded-md border border-ghost overflow-x-auto">
                  <pre className="text-sm font-mono text-on-surface-variant">
                    <code>{codingSubmission.payload_json?.code}</code>
                  </pre>
                </div>
                
                {(score as any).feedback_json && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-success/5 p-3 rounded-md flex items-center gap-3">
                      <CheckCircle size={20} className="text-success" />
                      <div>
                        <p className="text-xs text-tertiary uppercase">Passed Tests</p>
                        <p className="text-xl font-bold text-on-surface">
                          {(score as any).feedback_json.passed_tests} / {(score as any).feedback_json.total_tests}
                        </p>
                      </div>
                    </div>
                    <div className="bg-danger/5 p-3 rounded-md flex items-center gap-3">
                      <XCircle size={20} className="text-danger" />
                      <div>
                        <p className="text-xs text-tertiary uppercase">Failed Tests</p>
                        <p className="text-xl font-bold text-on-surface">
                          {(score as any).feedback_json.failed_tests}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            )}

            {mcqSubmission && (
              <Card className="space-y-4">
                <h3 className="text-lg font-bold">MCQ Review</h3>
                <div className="space-y-4">
                  {assessment.questions_json?.questions?.map((q: any, idx: number) => {
                    const candidateAnswer = mcqSubmission.payload_json?.answers?.[q.id];
                    const isCorrect = candidateAnswer === q.correct_answer;
                    return (
                      <div key={idx} className={`p-4 rounded-md border ${isCorrect ? 'border-success/20 bg-success/5' : 'border-danger/20 bg-danger/5'}`}>
                        <p className="text-sm font-medium mb-2">{idx + 1}. {q.question}</p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {q.options?.map((opt: string, i: number) => (
                            <div key={i} className={`p-2 rounded ${candidateAnswer === opt ? (isCorrect ? 'bg-success/20 font-bold' : 'bg-danger/20 font-bold') : 'bg-ghost'}`}>
                              {opt}
                            </div>
                          ))}
                        </div>
                        <div className="mt-3 text-xs space-y-1">
                          <p><span className="text-tertiary">Correct Answer:</span> <span className="text-success font-medium">{q.correct_answer}</span></p>
                          <p><span className="text-tertiary">Explanation:</span> {q.explanation}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
