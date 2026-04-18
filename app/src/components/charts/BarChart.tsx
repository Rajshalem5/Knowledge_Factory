import { cn } from '../../utils/cn';

interface BarChartProps {
  data: { label: string; value: number }[];
  maxValue?: number;
  className?: string;
}

export function BarChart({ data, maxValue, className }: BarChartProps) {
  const max = maxValue || Math.max(...data.map(d => d.value), 1);

  return (
    <div className={cn('space-y-2', className)}>
      {data.map((item, index) => (
        <div key={index} className="flex items-center gap-3">
          <span className="text-xs text-tertiary w-28 truncate text-right">{item.label}</span>
          <div className="flex-1 h-6 bg-surface-variant/30 rounded-sm overflow-hidden">
            <div
              className="h-full bg-secondary/60 rounded-sm transition-all duration-500 flex items-center px-2"
              style={{ width: `${Math.max((item.value / max) * 100, 2)}%` }}
            >
              <span className="text-[10px] font-bold text-on-secondary">{item.value}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
