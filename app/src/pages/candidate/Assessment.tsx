import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Badge } from '../../components/ui';
import { Timer } from '../../components/assessment/Timer';
import { CodeEditor } from '../../components/assessment/CodeEditor';
import { ProctoringOverlay } from '../../components/assessment/ProctoringOverlay';
import { useCodeExecution } from '../../hooks/useCodeExecution';
import { useActiveAssessments, useCompleteAssessment, useSubmitSection, useStartAssessment } from '../../hooks/useAssessment';
import { useMyCandidateProfile } from '../../hooks/useCandidates';
import { useProctoring } from '../../hooks/useProctoring';
import { Play, CheckSquare, AlertTriangle, Loader2, Zap, ShieldCheck } from 'lucide-react';
import { McqPanel } from '../../components/assessment/McqPanel';

const LANGUAGES = [
  { id: 'python', label: 'Python 3', version: '3.12.0' },
  { id: 'java',   label: 'Java',     version: '15.0.2' },
  { id: 'cpp',    label: 'C++',      version: '10.2.0' },
] as const;
type LangId = typeof LANGUAGES[number]['id'];

export default function Assessment() {
  const navigate = useNavigate();
  const [language, setLanguage] = useState<LangId>('python');
  
  // Section state for Round 2 (which now has both MCQ and Coding)
  const [activeSection, setActiveSection] = useState<'MCQ' | 'CODING'>('MCQ');

  // Multi-tab coding state
  const [activeTabIdx, setActiveTabIdx] = useState(0);
  const [codes, setCodes] = useState<Record<string, string>>({});
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});
  const [runOutputs, setRunOutputs] = useState<Record<string, { status: string; output: string } | null>>({});

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showStartModal, setShowStartModal] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [mcqAnswers, setMcqAnswers] = useState<Record<string, number>>({});

  const { runCode, isExecuting } = useCodeExecution();
  const { data: profile } = useMyCandidateProfile();
  const { data: activeAssessments, isLoading: assessmentsLoading, error: assessmentsError } = useActiveAssessments();
  const startAssessment = useStartAssessment();
  const completeAssessment = useCompleteAssessment();
  const submitSection = useSubmitSection();
  const hasTriggeredStart = useRef(false);

  const activeAssessment = activeAssessments?.[0];
  
  // A round is multi-section if it has both questions and problems in questions_json
  const questionsJson = (activeAssessment?.questions_json as any) || {};
  const hasMcq = Array.isArray(questionsJson.questions) && questionsJson.questions.length > 0;
  const hasCoding = Array.isArray(questionsJson.problems) && questionsJson.problems.length > 0;
  const isMultiSection = hasMcq && hasCoding;

  const codingProblems = questionsJson.problems || [];
  const currentProblem = codingProblems[activeTabIdx];

  // ── Proctoring ──
  const proctoring = useProctoring({
    assessmentAttemptId: activeAssessment?.id || '',
    onTerminated: (reason) => {
      alert(`Assessment terminated: ${reason}`);
      navigate('/portal');
    }
  });

  const { start: startProctoring } = proctoring;

  // ── Initialization ──
  useEffect(() => {
    if (hasTriggeredStart.current || assessmentsLoading || !activeAssessments) return;

    if (activeAssessments.length === 0 && profile) {
      hasTriggeredStart.current = true;
      const round = profile.status === 'ROUND2_PASSED' ? 'ROUND_3' : 'ROUND_2';
      startAssessment.mutate({ round }, {
        onSuccess: () => setShowStartModal(true),
        onError: () => setStartError('Failed to prepare assessment. Please go back and try again.'),
      });
    } else if (activeAssessments.length > 0 && proctoring.status === 'idle') {
      setShowStartModal(true);
    }
  }, [activeAssessments, assessmentsLoading, profile, startAssessment, proctoring.status]);

  // Load starter codes initially
  useEffect(() => {
    if (hasCoding && Object.keys(codes).length === 0) {
      const initialCodes: Record<string, string> = {};
      const initialInputs: Record<string, string> = {};
      codingProblems.forEach((p: any) => {
        initialCodes[p.id] = p.starter_code || '';
        initialInputs[p.id] = p.test_cases?.[0]?.input || '';
      });
      setCodes(initialCodes);
      setCustomInputs(initialInputs);
      
      if (profile?.language_choice) {
         const langId = profile.language_choice.toLowerCase();
         if (LANGUAGES.find(l => l.id === langId)) {
             setLanguage(langId as LangId);
         }
      }
    }
  }, [hasCoding, codingProblems, codes, profile]);

  if (assessmentsLoading || startAssessment.isPending) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--bg-base)]">
        <div className="text-center max-w-sm p-8">
          <Loader2 size={40} className="text-secondary mx-auto mb-4 animate-spin" />
          <h2 className="text-base font-semibold text-on-surface mb-1">
            {startAssessment.isPending ? 'Generating assessment...' : 'Preparing session...'}
          </h2>
        </div>
      </div>
    );
  }

  if (assessmentsError && !activeAssessments) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--bg-base)]">
        <div className="text-center p-8">
          <AlertTriangle size={48} className="text-warning mx-auto mb-4" />
          <h2 className="text-lg font-semibold mb-2">Unable to load assessment</h2>
          <Button onClick={() => navigate('/login')}>Go to Login</Button>
        </div>
      </div>
    );
  }

  if (!activeAssessment) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--bg-base)]">
        <Loader2 size={40} className="text-secondary mx-auto mb-4 animate-spin" />
      </div>
    );
  }

  const handleStartAssessment = async () => {
    setStartError(null);
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      }
      await startProctoring();
      setShowStartModal(false);
    } catch (err: any) {
      setStartError(err?.message || 'Failed to start assessment. Please try again.');
    }
  };

  const handleComplete = async () => {
    if (!window.confirm('Submit and complete this assessment? Your answers will be final.')) return;
    
    // Auto-save both sections before complete
    if (hasMcq) {
       await submitSection.mutateAsync({
         assessment_id: activeAssessment.id,
         section: 'MCQ',
         content: mcqAnswers,
       });
    }
    
    if (hasCoding) {
       await submitSection.mutateAsync({
         assessment_id: activeAssessment.id,
         section: 'CODING',
         content: { answers: codes } as any,
       });
    }
    
    completeAssessment.mutate(activeAssessment.id, {
      onSuccess: () => navigate('/portal'),
    });
  };

  const handleSaveDraft = async () => {
    setIsSubmitting(true);
    try {
      if (hasMcq) {
        await submitSection.mutateAsync({ assessment_id: activeAssessment.id, section: 'MCQ', content: mcqAnswers });
      }
      if (hasCoding) {
        await submitSection.mutateAsync({ assessment_id: activeAssessment.id, section: 'CODING', content: { answers: codes } as any });
      }
      alert('Progress saved successfully!');
    } catch (e: any) {
      alert('Failed to save progress.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRun = async () => {
    if (!currentProblem) return;
    const pid = currentProblem.id;
    setRunOutputs(prev => ({ ...prev, [pid]: null }));
    
    const result = await runCode({ language, code: codes[pid] || '', stdin: customInputs[pid] || '' });
    setRunOutputs(prev => ({ ...prev, [pid]: {
      status: result.status,
      output: result.status === 'SUCCESS' ? (result.stdout || '(no output)') : (result.stderr || 'Execution failed'),
    }}));
  };

  const handleCodeChange = (newCode: string) => {
    if (!currentProblem) return;
    setCodes(prev => ({ ...prev, [currentProblem.id]: newCode }));
  };

  // TODO: Re-enable CandidateDetail after type and hook issues are resolved
  // _handleInputChange was removed (unused — customInputs managed via setCustomInputs directly)


  const currentRunOutput = currentProblem ? runOutputs[currentProblem.id] : null;

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-base)]">
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 h-12 bg-[var(--bg-layer1)] shrink-0 border-b border-outline-variant">
        <div className="flex items-center gap-3">
          <Badge variant="warning">Round {activeAssessment.round === 'ROUND_3' ? '3' : '2'}</Badge>
          <span className="text-sm font-medium text-on-surface">
             {activeAssessment.round === 'ROUND_2' ? 'Qualifying Round (MCQ + Patterns)' : 'Advanced Coding Round'}
          </span>
        </div>
        
        {/* Section Switcher for Multi-Section Rounds */}
        {isMultiSection && (
          <div className="flex bg-[var(--bg-layer2)] p-1 rounded-lg border border-outline-variant">
            <button
              onClick={() => setActiveSection('MCQ')}
              className={`px-4 py-1 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
                activeSection === 'MCQ' ? 'bg-secondary text-white shadow-sm' : 'text-tertiary hover:text-on-surface'
              }`}
            >
              MCQs
            </button>
            <button
              onClick={() => setActiveSection('CODING')}
              className={`px-4 py-1 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
                activeSection === 'CODING' ? 'bg-secondary text-white shadow-sm' : 'text-tertiary hover:text-on-surface'
              }`}
            >
              Patterns
            </button>
          </div>
        )}

        <Timer initialSeconds={activeAssessment.time_limit ? activeAssessment.time_limit * 60 : 3600} className="!text-sm font-mono bg-ghost px-2 py-0.5 rounded border border-ghost" />
        
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={handleSaveDraft} isLoading={isSubmitting} className="h-8 text-[10px] uppercase font-bold tracking-widest">
            Save Draft
          </Button>
          <Button size="sm" onClick={handleComplete} isLoading={completeAssessment.isPending} disabled={completeAssessment.isPending} className="h-8 text-[10px] uppercase font-bold tracking-widest">
            <CheckSquare size={12} className="mr-1" /> Finish Round
          </Button>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-hidden relative">
        <ProctoringOverlay {...proctoring} />

        {/* MCQ Panel */}
        {activeSection === 'MCQ' && hasMcq && (
          <McqPanel 
            questions={questionsJson.questions} 
            onAnswersChange={setMcqAnswers}
            savedAnswers={mcqAnswers}
          />
        )}

        {/* Coding Panel */}
        {(activeSection === 'CODING' || (!hasMcq && hasCoding)) && (
          <div className="flex flex-col h-full overflow-hidden">
            {/* ── Question Tabs ── */}
            <div className="flex border-b border-outline-variant bg-[var(--bg-layer1)]">
              {codingProblems.map((p: any, idx: number) => (
                <button
                  key={p.id}
                  onClick={() => setActiveTabIdx(idx)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                    activeTabIdx === idx 
                      ? 'border-secondary text-secondary bg-secondary/5' 
                      : 'border-transparent text-tertiary hover:text-on-surface hover:bg-ghost'
                  }`}
                >
                  Pattern {idx + 1}
                  <Badge variant="success">
                    {p.points}pts
                  </Badge>
                </button>
              ))}
            </div>

            {/* ── Question Content ── */}
            <div className="flex-1 flex overflow-hidden">
              {!currentProblem ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center space-y-4">
                    <AlertTriangle size={48} className="text-warning mx-auto opacity-20" />
                    <p className="text-tertiary font-medium">Question data unavailable</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="w-1/2 flex flex-col overflow-y-auto border-r border-outline-variant p-5">
                    <h2 className="text-xl font-bold text-on-surface mb-2">{currentProblem.title}</h2>
                    <p className="text-xs text-tertiary mb-6 uppercase tracking-widest font-bold">Suggested time: {currentProblem.suggested_duration_mins} mins</p>
                    <p className="text-sm text-on-surface-variant whitespace-pre-wrap leading-relaxed mb-8 bg-ghost p-4 rounded-lg border border-ghost">
                      {currentProblem.description}
                    </p>
                    
                    <h3 className="text-[11px] font-bold uppercase tracking-widest text-secondary mb-4 flex items-center gap-2">
                       <Play size={12} /> Expected Output Format
                    </h3>
                    <div className="space-y-4">
                      {currentProblem.test_cases?.map((tc: any, i: number) => (
                        <div key={i} className="bg-[var(--bg-layer1)] border border-outline-variant p-4 rounded-lg font-mono">
                          {tc.input && (
                            <div className="mb-3">
                              <p className="text-[10px] text-tertiary uppercase font-bold mb-1">Input:</p>
                              <pre className="text-xs text-on-surface">{tc.input}</pre>
                            </div>
                          )}
                          <div>
                            <p className="text-[10px] text-tertiary uppercase font-bold mb-1">Output:</p>
                            <pre className="text-xs text-secondary">{tc.expectedOutput}</pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* ── Editor & Execution ── */}
                  <div className="w-1/2 flex flex-col bg-[var(--bg-layer1)]">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-outline-variant bg-[var(--bg-layer2)]">
                      <span className="text-[10px] uppercase font-black tracking-widest text-tertiary">Live Editor</span>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm" onClick={handleRun} disabled={isExecuting} className="h-7 text-[9px] uppercase font-bold">
                          {isExecuting ? <Loader2 size={10} className="animate-spin mr-1" /> : <Play size={10} className="mr-1" />}
                          Run Code
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex-1 overflow-hidden">
                      <CodeEditor 
                        value={codes[currentProblem.id] || ''} 
                        onChange={handleCodeChange} 
                        language={language === 'python' ? 'python' : language === 'java' ? 'java' : 'cpp'} 
                      />
                    </div>

                    <div className="h-64 flex flex-col border-t border-outline-variant bg-[var(--bg-base)]">
                      <div className="flex border-b border-outline-variant bg-[var(--bg-layer1)] shrink-0">
                        <div className="px-4 py-2 text-[10px] uppercase font-black tracking-widest text-on-surface border-b-2 border-secondary">
                          Console Output
                        </div>
                      </div>
                      <div className="flex-1 flex overflow-hidden">
                        <div className="flex-1 p-3 bg-black/20 overflow-y-auto">
                          {currentRunOutput ? (
                            <div className="font-mono text-sm">
                              <p className={`text-[10px] uppercase font-black mb-2 ${currentRunOutput.status === 'SUCCESS' ? 'text-success' : 'text-danger'}`}>
                                {currentRunOutput.status}
                              </p>
                              <pre className="whitespace-pre-wrap text-xs text-on-surface-variant leading-relaxed">
                                {currentRunOutput.output}
                              </pre>
                            </div>
                          ) : (
                            <div className="h-full flex items-center justify-center">
                               <p className="text-tertiary text-[10px] uppercase font-bold tracking-widest italic opacity-50">Press Run Code to see results</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Start Modal ── */}
      {showStartModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md px-4">
          <div className="bg-[var(--bg-base)] w-full max-w-md p-8 rounded-xl border border-outline-variant shadow-2xl space-y-6">
            <div className="text-center">
               <div className="w-16 h-16 bg-secondary/10 text-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap size={32} />
               </div>
               <h2 className="text-2xl font-bold text-on-surface">Ready to Start?</h2>
               <p className="text-sm text-tertiary mt-2">
                 Round 2 includes {hasMcq ? 'Multiple Choice Questions' : ''} {hasMcq && hasCoding ? 'and' : ''} {hasCoding ? 'Pattern Printing tasks' : ''}.
               </p>
            </div>

            <div className="bg-info/5 p-4 rounded-lg border border-info/20 space-y-3">
               <h4 className="text-xs font-bold text-info uppercase tracking-widest flex items-center gap-2">
                  <ShieldCheck size={14} /> Proctoring Guidelines
               </h4>
               <ul className="text-xs text-on-surface-variant space-y-2 list-disc pl-4">
                  <li>Full-screen mode is mandatory.</li>
                  <li>Tab switching will be flagged.</li>
                  <li>Camera must remain active and face clearly visible.</li>
                  <li>Do not use external help or AI assistants.</li>
               </ul>
            </div>

            {startError && (
              <div className="bg-danger/10 text-danger text-xs p-3 rounded-md border border-danger/20 flex items-center gap-2">
                <AlertTriangle size={14} />
                {startError}
              </div>
            )}

            <div className="flex flex-col gap-2 pt-2">
              <Button onClick={handleStartAssessment} className="w-full font-bold uppercase tracking-widest">Begin Session</Button>
              <Button onClick={() => navigate('/portal')} variant="ghost" className="w-full text-xs uppercase font-bold">Go Back</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
