import { Moon, Sun, Menu } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils/cn';

interface HeaderProps {
  onToggleSidebar?: () => void;
  title?: string;
  className?: string;
}

/* No-Line Rule: no border-bottom. Separation via surface tonal shift. */
export function Header({ onToggleSidebar, title, className }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className={cn(
      'flex items-center justify-between h-14 px-4 bg-[var(--bg-layer1)]',
      className,
    )}>
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button onClick={onToggleSidebar} className="text-tertiary hover:text-on-surface transition-colors">
            <Menu size={18} />
          </button>
        )}
        {title && <h1 className="text-sm font-semibold text-on-surface tracking-tight-display">{title}</h1>}
      </div>
      <button
        onClick={toggleTheme}
        className="p-2 rounded-md text-tertiary hover:text-on-surface hover:bg-surface-container-low transition-colors"
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
      </button>
    </header>
  );
}
