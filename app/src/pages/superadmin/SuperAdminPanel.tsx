import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Badge, Button } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { useOrganizations } from '../../hooks/useAnalytics';
import type { Organization, User } from '../../types';
import { Shield, Building2, Users, Settings } from 'lucide-react';
import { useState } from 'react';

const SAMPLE_ORGS: Organization[] = [
  { id: '1', name: 'Acme Corp', candidateCount: 450, activeHiringCycles: 3, plan: 'enterprise' },
  { id: '2', name: 'TechStart Inc', candidateCount: 230, activeHiringCycles: 1, plan: 'professional' },
  { id: '3', name: 'GlobalTech', candidateCount: 890, activeHiringCycles: 5, plan: 'enterprise' },
  { id: '4', name: 'DevHire Co', candidateCount: 120, activeHiringCycles: 2, plan: 'starter' },
];

const SAMPLE_USERS: (User & { organizationName: string })[] = [
  { id: '1', name: 'Alice Chen', email: 'alice@acme.com', role: 'admin', organizationName: 'Acme Corp' },
  { id: '2', name: 'Bob Singh', email: 'bob@techstart.com', role: 'hr', organizationName: 'TechStart Inc' },
  { id: '3', name: 'Carol Davis', email: 'carol@globaltech.com', role: 'interviewer', organizationName: 'GlobalTech' },
  { id: '4', name: 'Dan Park', email: 'dan@devhire.com', role: 'admin', organizationName: 'DevHire Co' },
  { id: '5', name: 'Eve Sharma', email: 'eve@acme.com', role: 'hr', organizationName: 'Acme Corp' },
];

const PLAN_COLORS: Record<string, 'success' | 'warning' | 'info'> = {
  starter: 'info',
  professional: 'warning',
  enterprise: 'success',
};

export default function SuperAdminPanel() {
  const { data: organizations } = useOrganizations();
  const [activeTab, setActiveTab] = useState<'orgs' | 'users'>('orgs');

  const orgs = organizations ?? SAMPLE_ORGS;

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
    { key: 'candidateCount', header: 'Candidates', render: o => <span className="font-mono text-xs">{o.candidateCount}</span> },
    { key: 'activeHiringCycles', header: 'Active Cycles', render: o => <span className="font-mono text-xs">{o.activeHiringCycles}</span> },
    {
      key: 'plan',
      header: 'Plan',
      render: (o) => <Badge variant={PLAN_COLORS[o.plan]}>{o.plan.charAt(0).toUpperCase() + o.plan.slice(1)}</Badge>,
    },
  ];

  const userColumns: Column<User & { organizationName: string }>[] = [
    {
      key: 'name',
      header: 'User',
      render: (u) => (
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center">
            <span className="text-[10px] font-bold text-secondary">{u.name.charAt(0)}</span>
          </div>
          <div>
            <p className="font-medium text-sm text-on-surface">{u.name}</p>
            <p className="text-[10px] text-tertiary">{u.email}</p>
          </div>
        </div>
      ),
    },
    { key: 'organizationName', header: 'Organization' },
    {
      key: 'role',
      header: 'Role',
      render: (u) => <Badge variant="default">{u.role}</Badge>,
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
                <p className="text-xl font-bold text-on-surface">{orgs.reduce((sum, o) => sum + o.candidateCount, 0).toLocaleString()}</p>
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
                <p className="text-xl font-bold text-on-surface">{orgs.reduce((sum, o) => sum + o.activeHiringCycles, 0)}</p>
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
              <Button size="sm">Add Organization</Button>
            </div>
            <DataTable
              columns={orgColumns}
              data={orgs}
              keyExtractor={o => o.id}
            />
          </Card>
        ) : (
          <Card padding="none">
            <div className="p-4 bg-[var(--bg-layer1)] flex items-center justify-between">
              <CardTitle>Users & Roles</CardTitle>
              <Button size="sm">Add User</Button>
            </div>
            <DataTable
              columns={userColumns}
              data={SAMPLE_USERS}
              keyExtractor={u => u.id}
            />
          </Card>
        )}
      </div>
    </AppShell>
  );
}
