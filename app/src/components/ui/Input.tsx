import { type InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

/* No-Line Rule: inputs use ghost border (15% opacity outline-variant), never solid borders */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-on-tertiary-container">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full rounded-md bg-[var(--bg-layer2)] px-3 py-2 text-sm text-on-surface',
            'placeholder:text-tertiary',
            'focus:outline-none focus:ring-2 focus:ring-secondary/30',
            'transition-colors duration-150',
            error ? 'ring-1 ring-danger/40' : 'ring-1 ring-[var(--border-ghost)]',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  },
);

Input.displayName = 'Input';
