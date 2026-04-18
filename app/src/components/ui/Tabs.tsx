import { useState, type ReactNode } from 'react';
import { cn } from '../../utils/cn';

interface Tab {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  className?: string;
}

/* No-Line Rule: no border-bottom on tab bar. Active tab uses secondary color indicator. */
export function Tabs({ tabs, defaultTab, className }: TabsProps) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id);
  const activeTab = tabs.find(t => t.id === active);

  return (
    <div className={className}>
      <div className="flex gap-1 mb-4 bg-[var(--bg-layer1)] rounded-md p-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors rounded-md',
              active === tab.id
                ? 'bg-[var(--bg-layer2)] text-secondary shadow-sm'
                : 'text-tertiary hover:text-on-surface-variant',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab?.content}
    </div>
  );
}
