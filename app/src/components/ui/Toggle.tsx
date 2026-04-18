import { cn } from '../../utils/cn';

interface ToggleProps {
  enabled: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  className?: string;
}

export function Toggle({ enabled, onChange, label, className }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      onClick={() => onChange(!enabled)}
      className={cn(
        'relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200',
        enabled ? 'bg-secondary' : 'bg-surface-variant',
        className,
      )}
    >
      <span
        className={cn(
          'inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform duration-200',
          enabled ? 'translate-x-4' : 'translate-x-0.5',
        )}
      />
      {label && <span className="sr-only">{label}</span>}
    </button>
  );
}
