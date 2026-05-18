import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  CheckCircle,
  BarChart3,
  Shield,
  UserCircle,
  Code,
  Factory,
  LogOut,
  Settings,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAuth } from '../../contexts/AuthContext';
import type { Role } from '../../types';
import { ROLE_LABELS } from '../../utils/roles';
import { useState, useRef, useEffect } from 'react';

interface NavItem {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
}

const NAV_ITEMS: Record<Role, NavItem[]> = {
  candidate: [
    { label: 'My Portal', path: '/portal', icon: UserCircle },
    { label: 'Assessment', path: '/assessment', icon: Code },
  ],
  hr: [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Candidates', path: '/candidates', icon: Users },
    { label: 'Selection', path: '/selection', icon: CheckCircle },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  ],
  interviewer: [
    { label: 'Interview Panel', path: '/interview', icon: MessageSquare },
    { label: 'Candidates', path: '/candidates', icon: Users },
  ],
  admin: [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Candidates', path: '/candidates', icon: Users },
    { label: 'Interviews', path: '/interview', icon: MessageSquare },
    { label: 'Selection', path: '/selection', icon: CheckCircle },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  ],
  superadmin: [
    { label: 'Super Admin', path: '/superadmin', icon: Shield },
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Candidates', path: '/candidates', icon: Users },
    { label: 'Selection', path: '/selection', icon: CheckCircle },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  ],
};

interface SidebarProps {
  collapsed?: boolean;
  className?: string;
}

/* Design.md: Admin/HR sidebar uses primary_container (#063342) as background.
   Icons are monochrome on-primary-container until hovered. No borders. */
export function Sidebar({ collapsed = false, className }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = user?.role;
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    }
    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserMenu]);

  if (!user || !role) return null;

  const items = NAV_ITEMS[role];

  const handleLogout = () => {
    setShowUserMenu(false);
    logout();
    navigate('/');
  };

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-primary-container',
        'transition-all duration-200',
        collapsed ? 'w-16' : 'w-60',
        className,
      )}
    >
      <div className={cn('flex items-center gap-2 px-4 h-14', collapsed && 'justify-center px-2')}>
        <Factory size={22} className="text-on-primary-container flex-shrink-0" />
        {!collapsed && <span className="font-bold text-sm text-on-primary-container">Knowledge Factory</span>}
      </div>

      <nav className="flex-1 py-3 overflow-y-auto">
        {items.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/portal' || item.path === '/dashboard' || item.path === '/superadmin' || item.path === '/interview'}
            className={({ isActive }) => cn(
              'flex items-center gap-3 mx-2 px-3 py-2 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-on-primary-container/15 text-secondary-container font-medium'
                : 'text-on-primary-container/70 hover:text-on-primary-container hover:bg-on-primary-container/8',
              collapsed && 'justify-center px-2',
            )}
          >
            <item.icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 relative" ref={menuRef}>
        <button
          onClick={() => setShowUserMenu(prev => !prev)}
          className={cn(
            'flex items-center gap-3 w-full text-left',
            collapsed && 'justify-center',
          )}
        >
          <div className="w-8 h-8 rounded-full bg-on-primary-container/15 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-bold text-on-primary-container">{user.name.charAt(0)}</span>
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-on-primary-container truncate">{user.name}</p>
              <p className="text-[10px] text-on-primary-container/60">{ROLE_LABELS[role]}</p>
            </div>
          )}
          {!collapsed && (
            <LogOut size={14} className="text-on-primary-container/40" />
          )}
        </button>

        {showUserMenu && (
          <div className={cn(
            'absolute bottom-full left-3 right-3 mb-1 rounded-md bg-surface-container-high ghost-shadow overflow-hidden',
            collapsed && 'left-1/2 -translate-x-1/2 w-40',
          )}>
            <button
              onClick={() => { setShowUserMenu(false); navigate('/settings'); }}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-on-surface hover:bg-surface-variant/20 transition-colors"
            >
              <Settings size={14} />
              Settings
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-danger hover:bg-surface-variant/20 transition-colors"
            >
              <LogOut size={14} />
              Logout
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
