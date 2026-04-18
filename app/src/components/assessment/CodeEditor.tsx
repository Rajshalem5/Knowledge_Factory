import { useState } from 'react';
import { cn } from '../../utils/cn';

interface CodeEditorProps {
  initialValue: string;
  onChange: (value: string) => void;
  className?: string;
}

export function CodeEditor({ initialValue, onChange, className }: CodeEditorProps) {
  const [value, setValue] = useState(initialValue);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    onChange(e.target.value);
  };

  const lineCount = value.split('\n').length;

  return (
    <div className={cn('flex h-full bg-primary font-mono text-sm', className)}>
      <div className="flex-shrink-0 py-4 px-2 text-right select-none">
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i} className="text-on-primary-container/40 leading-6 text-xs">
            {i + 1}
          </div>
        ))}
      </div>
      <textarea
        value={value}
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
