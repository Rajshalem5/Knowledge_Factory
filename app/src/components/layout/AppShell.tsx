import { useState, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { CandidateNav } from './CandidateNav';
import { useAuth } from '../../contexts/AuthContext';

interface AppShellProps {
  children: ReactNode;
  title?: string;
}

/* Design.md: Admin/HR gets high-density navy sidebar.
   Candidate gets centered "Glass" top-nav for a simpler, focused journey. */
export function AppShell({ children, title }: AppShellProps) {
  const { role } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  if (role === 'candidate') {
    return (
      <div className="flex flex-col h-screen overflow-hidden">
        <CandidateNav />
        <main className="flex-1 overflow-y-auto p-6 bg-[var(--bg-base)]">
          {children}
        </main>
      </div>
    );
  }

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
