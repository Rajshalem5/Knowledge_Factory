import { useEffect, useRef } from 'react';
import { cn } from '../../utils/cn';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  className?: string;
}

export function CodeEditor({ value = '', onChange, language, className }: CodeEditorProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Sync external value changes (language switch, question load)
  useEffect(() => {
    if (ref.current && ref.current.value !== value) {
      ref.current.value = value;
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  // Count lines from the textarea's current value (robust check)
  const currentContent = ref.current?.value ?? value ?? "";
  const lineCount = currentContent.split('\n').length;

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
        defaultValue={value}
        onChange={handleChange}
        spellCheck={false}
        className={cn(
          'flex-1 resize-none bg-transparent p-4 text-on-primary leading-6',
          'focus:outline-none caret-secondary',
          'placeholder:text-on-primary-container/30',
        )}
        placeholder={`Write your ${language || 'code'} here...`}
      />
    </div>
  );
}
