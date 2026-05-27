import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Upload,
  MessageSquare,
  CheckCircle,
  BarChart3,
  Shield,
  UserCircle,
  Code,
  FileText,
  Factory,
  LogOut,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAuth } from '../../contexts/AuthContext';
import type { Role } from '../../types';
import { ROLE_LABELS } from '../../utils/roles';

interface NavItem {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
}

const NAV_ITEMS: Record<Role, NavItem[]> = {
  candidate: [
    { label: 'Dashboard', path: '/portal', icon: LayoutDashboard },
    { label: 'Assessments', path: '/portal/assessments', icon: Code },
    { label: 'Results', path: '/portal/results', icon: CheckCircle },
    { label: 'Documents', path: '/portal/documents', icon: FileText },
    { label: 'Notifications', path: '/portal/notifications', icon: MessageSquare },
    { label: 'My Profile', path: '/portal/profile', icon: UserCircle },
  ],
  hr: [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Candidates', path: '/candidates', icon: Users },
    { label: 'Upload Center', path: '/uploads', icon: Upload },
    { label: 'Resumes', path: '/resumes', icon: FileText },
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
    { label: 'Upload Center', path: '/uploads', icon: Upload },
    { label: 'Resumes', path: '/resumes', icon: FileText },
    { label: 'Interviews', path: '/interview', icon: MessageSquare },
    { label: 'Selection', path: '/selection', icon: CheckCircle },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  ],
  superadmin: [
    { label: 'Super Admin', path: '/superadmin', icon: Shield },
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Candidates', path: '/candidates', icon: Users },
    { label: 'Upload Center', path: '/uploads', icon: Upload },
    { label: 'Resumes', path: '/resumes', icon: FileText },
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

  if (!user || !role) return null;

  const items = NAV_ITEMS[role];

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

      <div className="p-3">
        <div className={cn('flex items-center gap-3', collapsed && 'justify-center')}>
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
            <button
              onClick={() => { logout(); navigate('/'); }}
              className="text-on-primary-container/60 hover:text-danger transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
