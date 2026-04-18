import { useState, useEffect } from 'react';
import { cn } from '../../utils/cn';

interface TimerProps {
  initialSeconds: number;
  onExpire?: () => void;
  className?: string;
}

export function Timer({ initialSeconds, onExpire, className }: TimerProps) {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    if (seconds <= 0) {
      onExpire?.();
      return;
    }
    const timer = setInterval(() => setSeconds(s => s - 1), 1000);
    return () => clearInterval(timer);
  }, [seconds, onExpire]);

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const isLow = seconds < 300;

  return (
    <div className={cn(
      'text-2xl font-bold tabular-nums tracking-tight-display',
      isLow ? 'text-danger' : 'text-on-surface',
      className,
    )}>
      {hours > 0 && `${hours}:`}
      {String(minutes).padStart(2, '0')}:{String(secs).padStart(2, '0')}
    </div>
  );
}
