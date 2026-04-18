import { cn } from '../../utils/cn';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variants: Record<BadgeVariant, string> = {
  default: 'bg-surface-variant/40 text-on-surface-variant',
  success: 'bg-success-container/30 text-success',
  warning: 'bg-warning-container/30 text-warning',
  danger: 'bg-danger-container/30 text-danger',
  info: 'bg-info-container/30 text-info',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
