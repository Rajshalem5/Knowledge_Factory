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
      <div className={cn('p-6 text-center', className)}>
        <div className="space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-container-low mx-auto flex items-center justify-center">
            <CheckCircle size={20} className="text-tertiary" />
          </div>
          <p className="text-tertiary text-sm">Run your code to see test results</p>
        </div>
      </div>
    );
  }

  const passedCount = results.filter(r => r.passed).length;
  const failedCount = results.filter(r => !r.passed).length;

  return (
    <div className={cn('overflow-y-auto', className)}>
      <div className="p-4 border-b border-outline-variant/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success"></div>
              <span className="text-sm font-medium text-on-surface tracking-tight-display">Test Results</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <CheckCircle size={14} className="text-success" />
              <span className="text-success font-medium">{passedCount} passed</span>
            </div>
            {failedCount > 0 && (
              <div className="flex items-center gap-1">
                <XCircle size={14} className="text-danger" />
                <span className="text-danger font-medium">{failedCount} failed</span>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="divide-y divide-outline-variant/10">
        {results.map((result, index) => (
          <div key={index} className="p-4 hover:bg-surface-container-low/50 transition-colors">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                {result.passed ? (
                  <div className="w-5 h-5 rounded-full bg-success/20 flex items-center justify-center">
                    <CheckCircle size={12} className="text-success" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-danger/20 flex items-center justify-center">
                    <XCircle size={12} className="text-danger" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0 space-y-2">
                <p className="text-sm font-medium text-on-surface">{result.name}</p>
                {!result.passed && (
                  <div className="space-y-2 font-mono text-xs">
                    <div className="flex items-start gap-2">
                      <span className="text-tertiary min-w-[60px]">Expected:</span>
                      <code className="text-on-surface bg-surface-container-low px-2 py-1 rounded border">
                        {result.expected}
                      </code>
                    </div>
                    {result.actual && (
                      <div className="flex items-start gap-2">
                        <span className="text-tertiary min-w-[60px]">Got:</span>
                        <code className="text-danger bg-danger/10 px-2 py-1 rounded border border-danger/20">
                          {result.actual}
                        </code>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
