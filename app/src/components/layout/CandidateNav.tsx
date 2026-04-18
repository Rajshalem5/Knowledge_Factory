import { NavLink, useNavigate } from 'react-router-dom';
import { UserCircle, Code, Factory, LogOut, Moon, Sun } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

/* Design.md: Candidate gets a centered, "Glass" top-navigation bar
   to emphasize a simpler, more focused journey. */
export function CandidateNav() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  if (!user) return null;

  return (
    <nav className="glass sticky top-0 z-40 h-14 flex items-center justify-between px-6 ghost-shadow">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Factory size={20} className="text-primary-container" />
          <span className="font-bold text-sm text-on-surface tracking-tight-display">Knowledge Factory</span>
        </div>
        <div className="flex items-center gap-1">
          <NavLink
            to="/portal"
            end
            className={({ isActive }) => cn(
              'px-3 py-1.5 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-secondary/10 text-secondary font-medium'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low',
            )}
          >
            <UserCircle size={16} className="inline mr-1.5" />
            My Portal
          </NavLink>
          <NavLink
            to="/assessment"
            className={({ isActive }) => cn(
              'px-3 py-1.5 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-secondary/10 text-secondary font-medium'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low',
            )}
          >
            <Code size={16} className="inline mr-1.5" />
            Assessment
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-md text-tertiary hover:text-on-surface transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-secondary/15 flex items-center justify-center">
            <span className="text-[10px] font-bold text-secondary">{user.name.charAt(0)}</span>
          </div>
          <span className="text-xs font-medium text-on-surface">{user.name}</span>
        </div>
        <button
          onClick={() => { logout(); navigate('/'); }}
          className="text-tertiary hover:text-danger transition-colors"
          title="Logout"
        >
          <LogOut size={14} />
        </button>
      </div>
    </nav>
  );
}
