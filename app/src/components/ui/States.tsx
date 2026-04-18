import { Loader2, AlertCircle, Inbox } from 'lucide-react';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-tertiary">
      <Loader2 className="h-8 w-8 animate-spin mb-3" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function ErrorState({ message = 'Something went wrong', onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-tertiary">
      <AlertCircle className="h-8 w-8 mb-3 text-danger" />
      <p className="text-sm mb-3">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-sm text-secondary hover:text-secondary-container transition-colors">
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, description }: { icon?: typeof Inbox; title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-tertiary">
      <Icon className="h-10 w-10 mb-3" />
      <p className="text-sm font-medium text-on-surface-variant mb-1">{title}</p>
      {description && <p className="text-xs">{description}</p>}
    </div>
  );
}
