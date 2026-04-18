import type { Problem } from '../../types';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';

interface ProblemPanelProps {
  problem: Problem;
  className?: string;
}

const difficultyVariant = { easy: 'success' as const, medium: 'warning' as const, hard: 'danger' as const };

export function ProblemPanel({ problem, className }: ProblemPanelProps) {
  return (
    <div className={cn('h-full overflow-y-auto p-6', className)}>
      <div className="flex items-center gap-2 mb-4">
        <Badge variant={difficultyVariant[problem.difficulty]}>
          {problem.difficulty.charAt(0).toUpperCase() + problem.difficulty.slice(1)}
        </Badge>
      </div>
      <h2 className="text-xl font-semibold text-on-surface tracking-tight-display mb-4">
        {problem.title}
      </h2>
      <div className="prose prose-sm max-w-none text-on-surface-variant whitespace-pre-wrap leading-relaxed">
        {problem.description}
      </div>
      <div className="mt-6 pt-4 bg-[var(--bg-layer1)] -mx-6 px-6">
        <h3 className="text-[11px] font-medium uppercase tracking-architectural text-tertiary mb-3">
          Example Test Cases
        </h3>
        <div className="space-y-2">
          {problem.testCases.filter(tc => !tc.isHidden).map(tc => (
            <div key={tc.id} className="rounded-md bg-primary-container p-3 font-mono text-xs">
              <div className="text-on-primary-container/70">Input: <span className="text-on-primary-container">{tc.input}</span></div>
              <div className="text-on-primary-container/70">Expected: <span className="text-secondary">{tc.expectedOutput}</span></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
