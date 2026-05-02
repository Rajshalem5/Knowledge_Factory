import { useState } from 'react';
import { Button, Badge } from '../../components/ui';
import { Timer } from '../../components/assessment/Timer';
import { CodeEditor } from '../../components/assessment/CodeEditor';
import { useCodeExecution } from '../../hooks/useCodeExecution';
import { useQuestion } from '../../hooks/useQuestion';
import { Play, Send, ChevronDown, RefreshCw, CheckCircle, XCircle, Lock } from 'lucide-react';
import { api } from '../../api/client';
import type { EvaluationResponse } from '../../api/code-execution';

const LANGUAGES = [
  { id: 'python', label: 'Python 3', version: '3.12.0' },
  { id: 'java',   label: 'Java',     version: '15.0.2' },
  { id: 'cpp',    label: 'C++',      version: '10.2.0' },
] as const;
type LangId = typeof LANGUAGES[number]['id'];

const DIFFICULTIES = ['easy', 'medium', 'hard'] as const;

export default function Assessment() {
  const [language, setLanguage]         = useState<LangId>('python');
  const [code, setCode]                 = useState('# Click "Generate Question" to start');
  const [customInput, setCustomInput]   = useState('');
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [difficulty, setDifficulty]     = useState<string>('medium');
  const [topic, setTopic]               = useState('arrays and loops');
  const [evalResult, setEvalResult]     = useState<EvaluationResponse | null>(null);
  const [runOutput, setRunOutput]       = useState<{ status: string; output: string } | null>(null);

  const { question, isGenerating, generate } = useQuestion();
  const { runCode, isExecuting, isEvaluating } = useCodeExecution();

  // Generate question from AI
  const handleGenerate = async () => {
    setEvalResult(null);
    setRunOutput(null);
    const q = await generate({ topic, difficulty, num_public_cases: 2, num_private_cases: 4 });
    if (q) {
      // Pre-fill custom input with first public test case
      if (q.public_test_cases?.[0]) {
        setCustomInput(q.public_test_cases[0].input);
      }
      if (q.boilerplate?.[language]) {
        setCode(q.boilerplate[language]);
      } else if (q.boilerplate?.python) {
        setCode(q.boilerplate.python);
      }
    }
  };

  // Switch language → swap boilerplate if question loaded
  const handleLanguageChange = (lang: LangId) => {
    setLanguage(lang);
    setShowLangMenu(false);
    if (question?.boilerplate?.[lang]) {
      setCode(question.boilerplate[lang]);
    }
  };

  // RUN — execute with custom stdin, show raw output
  const handleRun = async () => {
    setRunOutput(null);
    setEvalResult(null);
    const result = await runCode({ language, code, stdin: customInput });
    setRunOutput({
      status: result.status,
      output: result.status === 'SUCCESS'
        ? (result.stdout || '(no output)')
        : (result.stderr || 'Execution failed'),
    });
  };

  // SUBMIT — evaluate against ALL test cases (public + private) via question id
  const handleSubmit = async () => {
    if (!question) return;
    setRunOutput(null);
    setEvalResult(null);
    try {
      const result = await api.post<EvaluationResponse>(
        `/code/evaluate-question/${question.id}`,
        { language, code, stdin: '' }
      );
      setEvalResult(result);
    } catch (e: unknown) {
      setRunOutput({ status: 'ERROR', output: (e as Error)?.message || 'Evaluation failed' });
    }
  };

  const currentLang = LANGUAGES.find(l => l.id === language)!;

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-base)]">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 h-12 bg-[var(--bg-layer1)] shrink-0">
        <div className="flex items-center gap-3">
          <Badge variant="warning">Round 2</Badge>
          <span className="text-sm font-medium text-on-surface">Coding Assessment</span>
        </div>
        <Timer initialSeconds={3600} className="!text-base" />
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleRun}
            disabled={isExecuting || !question}>
            <Play size={12} />
            {isExecuting ? 'Running...' : 'Run'}
          </Button>
          <Button size="sm" onClick={handleSubmit}
            isLoading={isEvaluating} disabled={!question}>
            <Send size={12} />
            Submit
          </Button>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Left: Problem Panel ── */}
        <div className="w-1/2 flex flex-col overflow-hidden border-r border-outline-variant">

          {/* Generate controls */}
          <div className="shrink-0 px-4 py-3 bg-[var(--bg-layer1)] flex flex-col gap-2">
            <div className="flex gap-2">
              <input
                value={topic}
                onChange={e => setTopic(e.target.value)}
                placeholder="Topic (e.g. binary search, graphs)"
                className="flex-1 bg-primary-container/30 text-on-surface text-xs rounded
                           px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-secondary/50
                           placeholder:text-tertiary"
              />
              <select
                value={difficulty}
                onChange={e => setDifficulty(e.target.value)}
                className="bg-primary-container/30 text-on-surface text-xs rounded
                           px-2 py-1.5 focus:outline-none"
              >
                {DIFFICULTIES.map(d => (
                  <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                ))}
              </select>
            </div>
            <Button variant="secondary" size="sm" onClick={handleGenerate}
              isLoading={isGenerating} className="w-full justify-center">
              <RefreshCw size={12} />
              {isGenerating ? 'Generating with AI...' : 'Generate Question'}
            </Button>
          </div>

          {/* Problem content */}
          <div className="flex-1 overflow-y-auto p-5">
            {!question ? (
              <div className="flex flex-col items-center justify-center h-full gap-3 text-tertiary">
                <RefreshCw size={32} className="opacity-30" />
                <p className="text-sm">Generate a question to begin</p>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant={
                    question.difficulty === 'easy' ? 'success' :
                    question.difficulty === 'hard' ? 'danger' : 'warning'
                  }>
                    {question.difficulty}
                  </Badge>
                </div>
                <h2 className="text-lg font-semibold text-on-surface mb-4">{question.title}</h2>
                <p className="text-sm text-on-surface-variant whitespace-pre-wrap leading-relaxed mb-6">
                  {question.description}
                </p>

                {/* Public test cases */}
                <div>
                  <h3 className="text-[11px] font-medium uppercase tracking-widest text-tertiary mb-3">
                    Example Test Cases
                  </h3>
                  <div className="space-y-2">
                    {question.public_test_cases.map((tc, i) => (
                      <div key={i} className="rounded-md bg-primary-container/40 p-3 font-mono text-xs">
                        <div className="text-on-primary-container/60 mb-1">
                          Input: <span className="text-on-primary-container whitespace-pre">{tc.input}</span>
                        </div>
                        <div className="text-on-primary-container/60">
                          Expected: <span className="text-secondary">{tc.expected_output}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Private test cases indicator */}
                <div className="mt-4 flex items-center gap-2 text-xs text-tertiary">
                  <Lock size={11} />
                  <span>4 hidden test cases used for final scoring</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* ── Right: Editor + Output ── */}
        <div className="w-1/2 flex flex-col bg-[var(--bg-layer1)]">

          {/* Toolbar */}
          <div className="flex items-center justify-between px-3 py-1.5 shrink-0">
            <span className="text-xs text-tertiary uppercase tracking-widest">Solution</span>
            <div className="relative">
              <button
                onClick={() => setShowLangMenu(v => !v)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium
                           bg-primary-container text-on-primary-container hover:opacity-80"
              >
                {currentLang.label}
                <ChevronDown size={11} />
              </button>
              {showLangMenu && (
                <div className="absolute right-0 top-full mt-1 z-50 min-w-[140px]
                                bg-[var(--bg-layer1)] border border-outline-variant
                                rounded-md shadow-lg overflow-hidden">
                  {LANGUAGES.map(lang => (
                    <button key={lang.id} onClick={() => handleLanguageChange(lang.id)}
                      className={`w-full text-left px-3 py-2 text-xs hover:bg-primary-container/40
                                  flex items-center justify-between
                                  ${lang.id === language ? 'text-secondary font-medium' : 'text-on-surface'}`}>
                      <span>{lang.label}</span>
                      <span className="text-tertiary text-[10px]">{lang.version}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Editor */}
          <div className="flex-1 overflow-hidden">
            <CodeEditor key={language} initialValue={code} onChange={setCode} className="h-full" />
          </div>

          {/* Custom input */}
          <div className="shrink-0 bg-[var(--bg-base)] px-3 pt-2 pb-1">
            <span className="text-[10px] text-tertiary uppercase tracking-widest">Custom Input (stdin)</span>
            <textarea
              value={customInput}
              onChange={e => setCustomInput(e.target.value)}
              rows={2}
              className="w-full mt-1 bg-primary-container/30 text-on-surface font-mono text-xs
                         rounded px-2 py-1.5 resize-none focus:outline-none focus:ring-1
                         focus:ring-secondary/50 placeholder:text-tertiary"
              placeholder="Input for Run button..."
            />
          </div>

          {/* Output panel */}
          <div className="h-44 bg-[var(--bg-base)] overflow-y-auto">

            {/* Run output */}
            {runOutput && (
              <div className="p-3">
                <span className={`text-[10px] uppercase tracking-widest font-medium
                  ${runOutput.status === 'SUCCESS' ? 'text-secondary' : 'text-danger'}`}>
                  {runOutput.status}
                </span>
                <pre className="mt-1 font-mono text-xs text-on-surface whitespace-pre-wrap">
                  {runOutput.output}
                </pre>
              </div>
            )}

            {/* Evaluation results */}
            {evalResult && (
              <div className="p-3">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-[10px] uppercase tracking-widest text-tertiary">Results</span>
                  <span className="text-xs text-secondary font-medium">
                    {evalResult.passed_tests}/{evalResult.total_tests} passed
                  </span>
                  <span className="text-xs font-medium text-on-surface">
                    Score: {evalResult.score_percentage}%
                  </span>
                </div>
                <div className="space-y-1">
                    {evalResult.test_results.map((tr, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      {tr.status === 'PASSED'
                        ? <CheckCircle size={12} className="text-secondary mt-0.5 shrink-0" />
                        : <XCircle size={12} className="text-danger mt-0.5 shrink-0" />
                      }
                      <span className={tr.status === 'PASSED' ? 'text-secondary' : 'text-danger'}>
                        Test {tr.test_number}
                      </span>
                      {tr.status !== 'PASSED' && (
                        <span className="text-tertiary font-mono">
                          expected {tr.expected} · got {tr.actual}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!runOutput && !evalResult && (
              <div className="p-4 text-xs text-tertiary">
                Run your code or submit to see results
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
