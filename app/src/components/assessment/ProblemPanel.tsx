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
        <Badge variant={difficultyVariant[problem.difficulty]} className="px-3 py-1">
          {problem.difficulty.charAt(0).toUpperCase() + problem.difficulty.slice(1)}
        </Badge>
      </div>
      <h2 className="text-2xl font-bold text-on-surface tracking-tight-display mb-6 leading-tight">
        {problem.title}
      </h2>
      <div className="prose prose-sm max-w-none text-on-surface-variant whitespace-pre-wrap leading-relaxed">
        {problem.description}
      </div>
      <div className="mt-8 pt-6 border-t border-outline-variant/20">
        <h3 className="text-lg font-semibold text-on-surface tracking-tight-display mb-4 flex items-center gap-2">
          <div className="w-1 h-4 bg-secondary rounded-full"></div>
          Example Test Cases
        </h3>
        <div className="space-y-3">
          {problem.testCases.filter(tc => !tc.isHidden).map(tc => (
            <div key={tc.id} className="rounded-lg bg-gradient-to-r from-surface-container-low to-surface-container-lowest border border-outline-variant/20 p-4 shadow-sm">
              <div className="space-y-2">
                <div className="flex items-start gap-3">
                  <span className="text-tertiary font-medium text-sm min-w-[50px] mt-1">Input:</span>
                  <code className="text-on-surface font-mono text-sm bg-surface-container-lowest px-3 py-2 rounded border flex-1">
                    {tc.input}
                  </code>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-tertiary font-medium text-sm min-w-[50px] mt-1">Output:</span>
                  <code className="text-secondary font-mono text-sm bg-secondary/10 px-3 py-2 rounded border border-secondary/20 flex-1">
                    {tc.expectedOutput}
                  </code>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
