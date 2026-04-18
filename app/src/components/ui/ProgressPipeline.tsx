import { cn } from '../../utils/cn';

interface PipelineStep {
  id: string;
  label: string;
}

interface ProgressPipelineProps {
  steps: PipelineStep[];
  currentStep: number;
  className?: string;
}

/* Design.md: Segmented Bar instead of line-and-dot.
   In-Progress: secondary with pulse. Completed: secondary-container. Empty: surface-variant. */
export function ProgressPipeline({ steps, currentStep, className }: ProgressPipelineProps) {
  return (
    <div className={cn('w-full', className)}>
      {/* Segmented bar */}
      <div className="flex w-full h-2 rounded-full overflow-hidden bg-surface-variant/50">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <div
              key={step.id}
              className={cn(
                'flex-1 mx-0.5 first:ml-0 last:mr-0 rounded-sm transition-all duration-300',
                isCompleted && 'bg-secondary-container',
                isCurrent && 'bg-secondary segment-pulse',
                !isCompleted && !isCurrent && 'bg-surface-variant/30',
              )}
            />
          );
        })}
      </div>
      {/* Labels */}
      <div className="flex justify-between mt-2">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <span
              key={step.id}
              className={cn(
                'text-[10px] font-medium flex-1 text-center transition-colors',
                isCompleted && 'text-secondary',
                isCurrent && 'text-secondary',
                !isCompleted && !isCurrent && 'text-tertiary',
              )}
            >
              {step.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
