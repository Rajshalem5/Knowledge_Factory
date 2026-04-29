import { useEffect, useRef } from 'react';
import { cn } from '../../utils/cn';

interface CodeEditorProps {
  initialValue: string;
  onChange: (value: string) => void;
  className?: string;
}

export function CodeEditor({ initialValue, onChange, className }: CodeEditorProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Sync external value changes (language switch, question load)
  useEffect(() => {
    if (ref.current && ref.current.value !== initialValue) {
      ref.current.value = initialValue;
    }
  }, [initialValue]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  // Count lines from the textarea's current value
  const lineCount = (ref.current?.value ?? initialValue).split('\n').length;

  return (
    <div className={cn('flex h-full bg-primary font-mono text-sm', className)}>
      <div className="flex-shrink-0 py-4 px-2 text-right select-none min-w-[2.5rem]">
        {Array.from({ length: Math.max(lineCount, 1) }, (_, i) => (
          <div key={i} className="text-on-primary-container/40 leading-6 text-xs">
            {i + 1}
          </div>
        ))}
      </div>
      <textarea
        ref={ref}
        defaultValue={initialValue}
        onChange={handleChange}
        spellCheck={false}
        className={cn(
          'flex-1 resize-none bg-transparent p-4 text-on-primary leading-6',
          'focus:outline-none caret-secondary',
          'placeholder:text-on-primary-container/30',
        )}
        placeholder="Write your code here..."
      />
    </div>
  );
}
