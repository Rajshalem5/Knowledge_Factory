import { useQuery } from '@tanstack/react-query';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { api } from '../../api/client';
import { Shield, Users, Building2, Settings } from 'lucide-react';
import { useState } from 'react';

interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  created_at: string | null;
}

const ROLE_COLORS: Record<string, 'info' | 'warning' | 'success' | 'default'> = {
  SUPERADMIN: 'warning',
  ADMIN: 'info',
  HR: 'success',
  INTERVIEWER: 'default',
};

const STATUS_COLORS: Record<string, 'success' | 'danger' | 'warning'> = {
  ACTIVE: 'success',
  INACTIVE: 'danger',
  PENDING: 'warning',
};

export default function SuperAdminPanel() {
  const [activeTab, setActiveTab] = useState<'users' | 'stats'>('users');

  const { data: adminUsers, isLoading, error } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.get<AdminUser[]>('/api/admin/users'),
  });

  if (isLoading) return <AppShell title="Super Admin"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Super Admin"><ErrorState message="Failed to load admin data" /></AppShell>;

  const users = adminUsers ?? [];

  const userColumns: Column<AdminUser>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (u) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center">
            <span className="text-xs font-bold text-secondary">{u.name.charAt(0)}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-on-surface">{u.name}</p>
            <p className="text-xs text-tertiary">{u.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (u) => <Badge variant={ROLE_COLORS[u.role] || 'default'}>{u.role}</Badge>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (u) => <Badge variant={STATUS_COLORS[u.status] || 'default'}>{u.status}</Badge>,
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (u) => <span className="text-xs text-tertiary">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</span>,
    },
  ];

  const activeUsers = users.filter(u => u.status === 'ACTIVE').length;

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
                <p className="text-xl font-bold text-on-surface">{users.length}</p>
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
                <p className="text-xl font-bold text-on-surface">{new Set(users.map(u => u.role)).size}</p>
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
          <Card padding="none">
            <div className="p-4 bg-[var(--bg-layer1)] flex items-center justify-between">
              <CardTitle>System Users</CardTitle>
            </div>
            <DataTable
              columns={userColumns}
              data={users}
              keyExtractor={u => u.id}
            />
          </Card>
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
