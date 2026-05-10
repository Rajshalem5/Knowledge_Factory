import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { useOrganizations } from '../../hooks/useAnalytics';
import type { Organization } from '../../types';
import { Shield, Building2, Users, Settings } from 'lucide-react';
import { useState } from 'react';

const PLAN_COLORS: Record<string, 'success' | 'warning' | 'info'> = {
  starter: 'info',
  professional: 'warning',
  enterprise: 'success',
};

export default function SuperAdminPanel() {
  const { data: organizations, isLoading, error } = useOrganizations();
  const [activeTab, setActiveTab] = useState<'orgs' | 'users'>('orgs');

  if (isLoading) return <AppShell title="Super Admin"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Super Admin"><ErrorState message="Failed to load organizations" /></AppShell>;

  const orgs = organizations ?? [];

  const orgColumns: Column<Organization>[] = [
    {
      key: 'name',
      header: 'Organization',
      render: (o) => (
        <div className="flex items-center gap-2">
          <Building2 size={14} className="text-secondary" />
          <span className="font-medium text-on-surface">{o.name}</span>
        </div>
      ),
    },
    { key: 'candidate_count', header: 'Candidates', render: o => <span className="font-mono text-xs">{o.candidate_count}</span> },
    { key: 'active_hiring_cycles', header: 'Active Cycles', render: o => <span className="font-mono text-xs">{o.active_hiring_cycles}</span> },
    {
      key: 'plan',
      header: 'Plan',
      render: (o) => <Badge variant={PLAN_COLORS[o.plan]}>{o.plan.charAt(0).toUpperCase() + o.plan.slice(1)}</Badge>,
    },
  ];

  return (
    <AppShell title="Super Admin">
      <div className="space-y-6">
        {/* Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Building2 size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Organizations</p>
                <p className="text-xl font-bold text-on-surface">{orgs.length}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Users size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Total Candidates</p>
                <p className="text-xl font-bold text-on-surface">{orgs.reduce((sum, o) => sum + o.candidate_count, 0).toLocaleString()}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Settings size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-architectural">Active Cycles</p>
                <p className="text-xl font-bold text-on-surface">{orgs.reduce((sum, o) => sum + o.active_hiring_cycles, 0)}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 bg-[var(--bg-layer1)] rounded-md p-1">
          <button
            onClick={() => setActiveTab('orgs')}
            className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${
              activeTab === 'orgs' ? 'bg-[var(--bg-base)] text-on-surface ghost-shadow' : 'text-tertiary'
            }`}
          >
            <Building2 size={14} className="inline mr-1.5" />
            Organizations
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${
              activeTab === 'users' ? 'bg-[var(--bg-base)] text-on-surface ghost-shadow' : 'text-tertiary'
            }`}
          >
            <Shield size={14} className="inline mr-1.5" />
            Users & Roles
          </button>
        </div>

        {activeTab === 'orgs' ? (
          <Card padding="none">
            <div className="p-4 bg-[var(--bg-layer1)] flex items-center justify-between">
              <CardTitle>Organizations</CardTitle>
            </div>
            <DataTable
              columns={orgColumns}
              data={orgs}
              keyExtractor={o => o.id}
            />
          </Card>
        ) : (
          <Card padding="none">
            <div className="p-4 bg-[var(--bg-layer1)]">
              <CardTitle>Users &amp; Roles</CardTitle>
            </div>
            <ErrorState message="User management requires backend integration" />
          </Card>
        )}
      </div>
    </AppShell>
  );
}
