
import { useState } from 'react';
import { Button, Badge } from '../ui';
import { CheckCircle, AlertCircle } from 'lucide-react';

interface McqQuestion {
  id: string;
  question: string;
  options: string[];
  category: string;
  difficulty: string;
}

interface McqPanelProps {
  questions: McqQuestion[];
  onAnswersChange: (answers: Record<string, number>) => void;
  savedAnswers?: Record<string, number>;
}

export function McqPanel({ questions, onAnswersChange, savedAnswers = {} }: McqPanelProps) {
  const [answers, setAnswers] = useState<Record<string, number>>(savedAnswers);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleSelect = (questionId: string, optionIndex: number) => {
    const newAnswers = { ...answers, [questionId]: optionIndex };
    setAnswers(newAnswers);
    onAnswersChange(newAnswers);
  };

  const currentQuestion = questions[currentIndex];
  if (!currentQuestion || questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-10 text-center">
        <AlertCircle size={48} className="text-tertiary mb-4 opacity-20" />
        <h3 className="text-lg font-medium text-on-surface mb-2">No questions available</h3>
        <p className="text-sm text-tertiary max-w-xs">
          We encountered an issue loading questions for this section. Please contact support.
        </p>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const totalCount = questions.length;
  const progress = (answeredCount / totalCount) * 100;

  return (
    <div className="flex flex-col h-full bg-[var(--bg-base)]">
      {/* ── MCQ Progress Header ── */}
      <div className="px-6 py-4 bg-[var(--bg-layer1)] border-b border-outline-variant shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-on-surface">MCQ Section</h2>
            <p className="text-xs text-tertiary">Answer all questions to complete the round</p>
          </div>
          <div className="text-right">
            <span className="text-sm font-bold text-secondary">{answeredCount}</span>
            <span className="text-sm text-tertiary"> / {totalCount} Answered</span>
          </div>
        </div>
        <div className="h-1.5 w-full bg-secondary/10 rounded-full overflow-hidden">
          <div 
            className="h-full bg-secondary transition-all duration-300" 
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* ── Question Navigator (Left Sidebar) ── */}
        <div className="w-64 border-r border-outline-variant bg-[var(--bg-layer1)] overflow-y-auto p-4 hidden md:block">
          <h3 className="text-[11px] font-bold uppercase tracking-widest text-tertiary mb-4">Questions</h3>
          <div className="grid grid-cols-4 gap-2">
            {questions.map((q, idx) => (
              <button
                key={q.id}
                onClick={() => setCurrentIndex(idx)}
                className={`
                  h-10 w-10 rounded flex items-center justify-center text-sm font-medium transition-all
                  ${currentIndex === idx ? 'ring-2 ring-secondary ring-offset-2 ring-offset-[var(--bg-layer1)]' : ''}
                  ${answers[q.id] !== undefined ? 'bg-secondary text-on-secondary' : 'bg-[var(--bg-layer2)] text-tertiary hover:bg-secondary/10 hover:text-secondary'}
                `}
              >
                {idx + 1}
              </button>
            ))}
          </div>
        </div>

        {/* ── Main Question Area ── */}
        <div className="flex-1 overflow-y-auto p-6 md:p-10">
          <div className="max-w-3xl mx-auto space-y-8">
            {/* Question Card */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Badge variant="info" className="uppercase">{currentQuestion.category}</Badge>
                <Badge 
                  variant={currentQuestion.difficulty === 'easy' ? 'success' : currentQuestion.difficulty === 'hard' ? 'danger' : 'warning'}
                  className="uppercase"
                >
                  {currentQuestion.difficulty}
                </Badge>
                <span className="text-xs text-tertiary">Question {currentIndex + 1} of {totalCount}</span>
              </div>

              <h1 className="text-xl md:text-2xl font-medium text-on-surface leading-snug">
                {currentQuestion.question}
              </h1>

              <div className="space-y-3 pt-4">
                {currentQuestion.options.map((option, idx) => {
                  const isSelected = answers[currentQuestion.id] === idx;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSelect(currentQuestion.id, idx)}
                      className={`
                        w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left group
                        ${isSelected 
                          ? 'bg-secondary/10 border-secondary text-on-surface' 
                          : 'bg-[var(--bg-layer2)] border-outline-variant text-on-surface-variant hover:border-secondary/40 hover:bg-secondary/5'}
                      `}
                    >
                      <div className={`
                        shrink-0 h-6 w-6 rounded-full border-2 flex items-center justify-center transition-colors
                        ${isSelected ? 'border-secondary bg-secondary text-on-secondary' : 'border-tertiary group-hover:border-secondary'}
                      `}>
                        {isSelected ? <CheckCircle size={14} /> : <div className="h-1.5 w-1.5 rounded-full bg-transparent" />}
                      </div>
                      <span className="text-base">{option}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-10 border-t border-outline-variant">
              <Button
                variant="secondary"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex(prev => prev - 1)}
              >
                Previous
              </Button>
              <div className="flex gap-2">
                {currentIndex < totalCount - 1 ? (
                  <Button
                    onClick={() => setCurrentIndex(prev => prev + 1)}
                  >
                    Next Question
                  </Button>
                ) : (
                  <div className="flex items-center gap-2 text-secondary text-sm font-medium">
                    <AlertCircle size={16} />
                    All questions viewed
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
