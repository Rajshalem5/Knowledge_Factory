import { cn } from '../../utils/cn';
import { CheckCircle, XCircle } from 'lucide-react';

interface TestResult {
  name: string;
  passed: boolean;
  input: string;
  expected: string;
  actual?: string;
}

interface TestOutputProps {
  results: TestResult[];
  className?: string;
}

/* No-Line Rule: no dividers between test results. Tonal separation only. */
export function TestOutput({ results, className }: TestOutputProps) {
  if (results.length === 0) {
    return (
      <div className={cn('p-4 text-sm text-tertiary', className)}>
        Run your code to see test results
      </div>
    );
  }

  return (
    <div className={cn('overflow-y-auto', className)}>
      <div className="p-3 flex items-center gap-2">
        <span className="text-[11px] font-medium text-tertiary uppercase tracking-architectural">
          Test Results
        </span>
        <span className="text-xs text-secondary">{results.filter(r => r.passed).length} passed</span>
        <span className="text-xs text-tertiary">/</span>
        <span className="text-xs text-danger">{results.filter(r => !r.passed).length} failed</span>
      </div>
      <div>
        {results.map((result, index) => (
          <div key={index} className={cn('p-3 flex items-start gap-2', index % 2 !== 0 && 'bg-[var(--bg-layer1)]')}>
            {result.passed ? (
              <CheckCircle size={14} className="text-secondary mt-0.5 flex-shrink-0" />
            ) : (
              <XCircle size={14} className="text-danger mt-0.5 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-on-surface">{result.name}</p>
              {!result.passed && (
                <div className="mt-1 font-mono text-[10px] space-y-0.5">
                  <div className="text-on-surface-variant">Expected: {result.expected}</div>
                  {result.actual && <div className="text-danger">Got: {result.actual}</div>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
