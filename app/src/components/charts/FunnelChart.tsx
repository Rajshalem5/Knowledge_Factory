import type { FunnelData } from '../../types';
import { cn } from '../../utils/cn';

interface FunnelChartProps {
  data: FunnelData;
  className?: string;
}

const LABELS: { key: keyof FunnelData; label: string }[] = [
  { key: 'applied', label: 'Applied' },
  { key: 'eligible', label: 'Eligible' },
  { key: 'assessed', label: 'Assessed' },
  { key: 'interviewed', label: 'Interviewed' },
  { key: 'selected', label: 'Selected' },
];

export function FunnelChart({ data, className }: FunnelChartProps) {
  const values = LABELS.map(({ key }) => data[key] ?? 0);
  const max = Math.max(...values, 1);

  return (
    <div className={cn('space-y-3', className)}>
      {LABELS.map(({ key, label }, index) => {
        const value = data[key] ?? 0;
        const width = Math.max((value / max) * 100, 4);
        const isLast = index === LABELS.length - 1;

        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs font-medium text-tertiary w-24 text-right">{label}</span>
            <div className="flex-1 h-8 bg-surface-variant/30 rounded-sm overflow-hidden relative">
              <div
                className={cn(
                  'h-full rounded-sm flex items-center px-3 transition-all duration-500',
                  isLast ? 'bg-secondary-container' : 'bg-secondary/70',
                )}
                style={{ width: `${width}%` }}
              >
                <span className="text-xs font-bold text-on-secondary">{value}</span>
              </div>
            </div>
            <span className="text-xs text-tertiary w-12">
              {Math.round((value / max) * 100)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
