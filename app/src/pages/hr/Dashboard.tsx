import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Upload, Search } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Button, Select, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { FunnelChart } from '../../components/charts/FunnelChart';
import { useCandidates } from '../../hooks/useCandidates';
import { useFunnelData } from '../../hooks/useAnalytics';
import { STATUS_LABELS } from '../../utils/roles';
import type { Candidate } from '../../types';

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'applied', label: 'Applied' },
  { value: 'eligible', label: 'Eligible' },
  { value: 'round1', label: 'Round 1' },
  { value: 'round2', label: 'Round 2' },
  { value: 'round3', label: 'Round 3' },
  { value: 'interviewed', label: 'Interviewed' },
  { value: 'selected', label: 'Selected' },
  { value: 'rejected', label: 'Rejected' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [branchFilter] = useState('');

  const { data: candidatesData, isLoading, error } = useCandidates({
    page,
    pageSize: 10,
    search: search || undefined,
    status: statusFilter || undefined,
    branch: branchFilter || undefined,
  });

  const { data: funnelData, isLoading: funnelLoading } = useFunnelData();

  const columns: Column<Candidate>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (c) => <span className="font-medium text-on-surface">{c.name}</span>,
    },
    { key: 'college', header: 'College' },
    { key: 'branch', header: 'Branch' },
    {
      key: 'cgpa',
      header: 'CGPA',
      render: (c) => <span className="font-mono text-xs">{c.cgpa.toFixed(1)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (c) => (
        <Badge variant={c.status === 'selected' ? 'success' : c.status === 'rejected' ? 'danger' : 'default'}>
          {STATUS_LABELS[c.status]}
        </Badge>
      ),
    },
  ];

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        {/* Stats */}
        {candidatesData ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-secondary/10">
                  <Users size={18} className="text-secondary" />
                </div>
                <div>
                  <p className="text-xs text-tertiary uppercase tracking-architectural">Total Candidates</p>
                  <p className="text-xl font-bold text-on-surface">{candidatesData.pagination.total}</p>
                </div>
              </div>
            </Card>
          </div>
        ) : null}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Funnel */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Hiring Funnel</CardTitle>
            </CardHeader>
            {funnelLoading ? (
              <LoadingState message="Loading funnel..." />
            ) : funnelData ? (
              <FunnelChart data={funnelData} />
            ) : (
              <ErrorState message="Funnel data unavailable" />
            )}
          </Card>

          {/* Candidate Table */}
          <Card padding="none" className="lg:col-span-2">
            <div className="p-4 bg-[var(--bg-layer1)]">
              <div className="flex items-center justify-between mb-3">
                <CardTitle>Candidates</CardTitle>
                <Button variant="secondary" size="sm">
                  <Upload size={14} />
                  Bulk Upload
                </Button>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" />
                  <input
                    type="text"
                    placeholder="Search candidates..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50"
                  />
                </div>
                <Select
                  options={STATUS_OPTIONS}
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="w-36"
                />
              </div>
            </div>
            {isLoading ? (
              <LoadingState />
            ) : error ? (
              <ErrorState message="Failed to load candidates" />
            ) : candidatesData ? (
              <DataTable
                columns={columns}
                data={candidatesData.data}
                keyExtractor={c => c.id}
                page={page}
                totalPages={candidatesData.pagination.totalPages}
                onPageChange={setPage}
                onRowClick={c => navigate(`/candidates/${c.id}`)}
              />
            ) : null}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
