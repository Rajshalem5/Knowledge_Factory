import { useState, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAuth } from '../../contexts/AuthContext';

interface AppShellProps {
  children: ReactNode;
  title?: string;
}

/* Design.md: Admin/HR gets high-density navy sidebar.
   Candidate gets the same professional navigation for a modern ATS feel. */
export function AppShell({ children, title }: AppShellProps) {
  const { user } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  if (!user) return <>{children}</>;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          title={title}
          onToggleSidebar={() => setSidebarCollapsed(prev => !prev)}
        />
        <main className="flex-1 overflow-y-auto p-6 bg-[var(--bg-base)]">
          {children}
        </main>
      </div>
    </div>
  );
}
