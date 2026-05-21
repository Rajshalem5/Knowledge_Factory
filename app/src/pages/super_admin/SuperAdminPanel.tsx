import { useQuery } from '@tanstack/react-query';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, LoadingState, ErrorState } from '../../components/ui';
import { adminApi } from '../../api/admin';
import { Shield, Users, Building2, Settings } from 'lucide-react';
import { useState } from 'react';
import { UserManagement } from '../../components/admin/UserManagement';

export default function SuperAdminPanel() {
  const [activeTab, setActiveTab] = useState<'users' | 'stats'>('users');

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-users-stats'],
    queryFn: () => adminApi.getUsers(),
  });

  if (isLoading) return <AppShell title="Super Admin"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Super Admin"><ErrorState message="Failed to load admin data" /></AppShell>;

  const userList = users ?? [];
  const activeUsers = userList.filter(u => u.status === 'ACTIVE').length;

  return (
    <AppShell title="Super Admin">
      <div className="space-y-6">
        {/* Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Users size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Total Users</p>
                <p className="text-xl font-bold text-on-surface">{userList.length}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Shield size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Active Users</p>
                <p className="text-xl font-bold text-on-surface">{activeUsers}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Settings size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Roles</p>
                <p className="text-xl font-bold text-on-surface">{new Set(userList.map(u => u.role)).size}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 bg-[var(--bg-layer1)] rounded-md p-1">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${
              activeTab === 'users' ? 'bg-[var(--bg-base)] text-on-surface ghost-shadow' : 'text-tertiary'
            }`}
          >
            <Shield size={14} className="inline mr-1.5" />
            Users & Roles
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${
              activeTab === 'stats' ? 'bg-[var(--bg-base)] text-on-surface ghost-shadow' : 'text-tertiary'
            }`}
          >
            <Building2 size={14} className="inline mr-1.5" />
            Pipeline Summary
          </button>
        </div>

        {activeTab === 'users' ? (
          <UserManagement manageAdmins={true} />
        ) : (
          <Card>
            <div className="p-4">
              <CardTitle>Pipeline Summary</CardTitle>
              <p className="text-sm text-tertiary mt-2">
                Overall hiring pipeline analytics are available on the Analytics Dashboard.
              </p>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
