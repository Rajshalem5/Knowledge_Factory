import type { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: { value: number; positive: boolean };
  icon: LucideIcon;
  className?: string;
}

/* No-Line Rule: no border. Tonal surface lift. Use secondary for AI-powered insights. */
export function StatCard({ label, value, change, icon: Icon, className }: StatCardProps) {
  return (
    <div className={cn(
      'rounded-md bg-[var(--bg-layer2)] p-5 ghost-shadow',
      className,
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-medium text-tertiary uppercase tracking-architectural">{label}</p>
          <p className="mt-2 text-2xl font-bold text-on-surface tracking-tight-display">{value}</p>
          {change && (
            <p className={cn(
              'mt-1 text-xs font-medium',
              change.positive ? 'text-secondary' : 'text-danger',
            )}>
              {change.positive ? '+' : ''}{change.value}%
            </p>
          )}
        </div>
        <div className="p-2 rounded-md bg-secondary/10">
          <Icon size={18} className="text-secondary" />
        </div>
      </div>
    </div>
  );
}
