import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Upload, Search, Play, Filter, X, Download } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Button, Select, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { FunnelChart } from '../../components/charts/FunnelChart';
import { useCandidates } from '../../hooks/useCandidates';
import { useFunnelData } from '../../hooks/useAnalytics';
import { useRunScreening, usePipelineStats } from '../../hooks/useScreening';
import { STATUS_LABELS } from '../../utils/roles';
import { exportToCsv } from '../../utils/csv';
import type { Candidate, CandidateStatus } from '../../types';

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
  const [branchFilter, setBranchFilter] = useState('');
  const [collegeFilter, setCollegeFilter] = useState('');
  const [minCgpaOverride, setMinCgpaOverride] = useState('');
  const [cgpaMinFilter, setCgpaMinFilter] = useState('');
  const [cgpaMaxFilter, setCgpaMaxFilter] = useState('');
  const [languageChoiceFilter, setLanguageChoiceFilter] = useState('');
  const [hasResumeFilter, setHasResumeFilter] = useState('');
  const [hasGovtIdFilter, setHasGovtIdFilter] = useState('');
  const [createdAfterFilter, setCreatedAfterFilter] = useState('');
  const [createdBeforeFilter, setCreatedBeforeFilter] = useState('');
  const [passedOutYearFilter, setPassedOutYearFilter] = useState('');
  const [passedOutYearMinFilter, setPassedOutYearMinFilter] = useState('');
  const [passedOutYearMaxFilter, setPassedOutYearMaxFilter] = useState('');
  const [emailVerifiedFilter, setEmailVerifiedFilter] = useState('');
  const [phoneFilter, setPhoneFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [nameFilter, setNameFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { data: candidatesData, isLoading, error } = useCandidates({
    page,
    limit: 10,
    search: search || undefined,
    status: statusFilter || undefined,
    name: nameFilter || undefined,
    branch: branchFilter || undefined,
    college: collegeFilter || undefined,
    cgpa_min: cgpaMinFilter ? parseFloat(cgpaMinFilter) : undefined,
    cgpa_max: cgpaMaxFilter ? parseFloat(cgpaMaxFilter) : undefined,
    language_choice: languageChoiceFilter || undefined,
    has_resume: hasResumeFilter ? hasResumeFilter === 'true' : undefined,
    has_govt_id: hasGovtIdFilter ? hasGovtIdFilter === 'true' : undefined,
    created_after: createdAfterFilter || undefined,
    created_before: createdBeforeFilter || undefined,
    passed_out_year: passedOutYearFilter ? parseInt(passedOutYearFilter, 10) : undefined,
    passed_out_year_min: passedOutYearMinFilter ? parseInt(passedOutYearMinFilter, 10) : undefined,
    passed_out_year_max: passedOutYearMaxFilter ? parseInt(passedOutYearMaxFilter, 10) : undefined,
    email_verified: emailVerifiedFilter ? emailVerifiedFilter === 'true' : undefined,
    phone: phoneFilter || undefined,
    email: emailFilter || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const { data: funnelData, isLoading: funnelLoading } = useFunnelData(
    search || branchFilter || collegeFilter || languageChoiceFilter || cgpaMinFilter ||
    cgpaMaxFilter || hasResumeFilter || hasGovtIdFilter || createdAfterFilter ||
    createdBeforeFilter || passedOutYearFilter || passedOutYearMinFilter || passedOutYearMaxFilter ||
    emailVerifiedFilter || phoneFilter || emailFilter || nameFilter
      ? {
          branch: branchFilter || undefined,
          college: collegeFilter || undefined,
          search: search || undefined,
          name: nameFilter || undefined,
          language_choice: languageChoiceFilter || undefined,
          cgpa_min: cgpaMinFilter ? parseFloat(cgpaMinFilter) : undefined,
          cgpa_max: cgpaMaxFilter ? parseFloat(cgpaMaxFilter) : undefined,
          has_resume: hasResumeFilter ? hasResumeFilter === 'true' : undefined,
          has_govt_id: hasGovtIdFilter ? hasGovtIdFilter === 'true' : undefined,
          created_after: createdAfterFilter || undefined,
          created_before: createdBeforeFilter || undefined,
          passed_out_year: passedOutYearFilter ? parseInt(passedOutYearFilter, 10) : undefined,
          passed_out_year_min: passedOutYearMinFilter ? parseInt(passedOutYearMinFilter, 10) : undefined,
          passed_out_year_max: passedOutYearMaxFilter ? parseInt(passedOutYearMaxFilter, 10) : undefined,
          email_verified: emailVerifiedFilter ? emailVerifiedFilter === 'true' : undefined,
          phone: phoneFilter || undefined,
          email: emailFilter || undefined,
        }
      : undefined
  );
  const runScreening = useRunScreening();
  const { data: pipelineStats } = usePipelineStats(
    (() => {
      const p: Record<string, string | number | boolean> = {};
      if (branchFilter) p.branch = branchFilter;
      if (collegeFilter) p.college = collegeFilter;
      if (languageChoiceFilter) p.language_choice = languageChoiceFilter;
      if (cgpaMinFilter) p.cgpa_min = parseFloat(cgpaMinFilter);
      if (cgpaMaxFilter) p.cgpa_max = parseFloat(cgpaMaxFilter);
      if (hasResumeFilter) p.has_resume = hasResumeFilter === 'true';
      if (hasGovtIdFilter) p.has_govt_id = hasGovtIdFilter === 'true';
      if (createdAfterFilter) p.created_after = createdAfterFilter;
      if (createdBeforeFilter) p.created_before = createdBeforeFilter;
      if (passedOutYearFilter) p.passed_out_year = parseInt(passedOutYearFilter, 10);
      if (passedOutYearMinFilter) p.passed_out_year_min = parseInt(passedOutYearMinFilter, 10);
      if (passedOutYearMaxFilter) p.passed_out_year_max = parseInt(passedOutYearMaxFilter, 10);
      if (emailVerifiedFilter) p.email_verified = emailVerifiedFilter === 'true';
      if (phoneFilter) p.phone = phoneFilter;
      if (emailFilter) p.email = emailFilter;
      if (nameFilter) p.name = nameFilter;
      if (search) p.search = search;
      return Object.keys(p).length > 0 ? p : undefined;
    })()
  );

  const handleRunScreening = () => {
    const params: Record<string, string | number | boolean> = {};
    if (branchFilter) params.branch = branchFilter;
    if (collegeFilter) params.college = collegeFilter;
    if (languageChoiceFilter) params.language_choice = languageChoiceFilter;
    if (minCgpaOverride) params.min_cgpa_override = parseFloat(minCgpaOverride);
    if (cgpaMinFilter) params.cgpa_min = parseFloat(cgpaMinFilter);
    if (cgpaMaxFilter) params.cgpa_max = parseFloat(cgpaMaxFilter);
    if (hasResumeFilter) params.has_resume = hasResumeFilter === 'true';
    if (hasGovtIdFilter) params.has_govt_id = hasGovtIdFilter === 'true';
    if (createdAfterFilter) params.created_after = createdAfterFilter;
    if (createdBeforeFilter) params.created_before = createdBeforeFilter;
    if (passedOutYearFilter) params.passed_out_year = parseInt(passedOutYearFilter, 10);
    if (passedOutYearMinFilter) params.passed_out_year_min = parseInt(passedOutYearMinFilter, 10);
    if (passedOutYearMaxFilter) params.passed_out_year_max = parseInt(passedOutYearMaxFilter, 10);
    if (emailVerifiedFilter) params.email_verified = emailVerifiedFilter === 'true';
    if (phoneFilter) params.phone = phoneFilter;
    if (emailFilter) params.email = emailFilter;
    if (nameFilter) params.name = nameFilter;
    if (search) params.search = search;
    runScreening.mutate(
      Object.keys(params).length > 0 ? params : undefined
    );
  };

  const handleDownloadCsv = () => {
    if (!candidatesData?.data?.length) return;
    const cols = [
      { key: 'name', header: 'Name' },
      { key: 'email', header: 'Email' },
      { key: 'college', header: 'College' },
      { key: 'branch', header: 'Branch' },
      { key: 'cgpa', header: 'CGPA' },
      { key: 'passed_out_year', header: 'Passed Out Year' },
      { key: 'language_choice', header: 'Language' },
      { key: 'display_status', header: 'Status' },
      { key: 'created_at', header: 'Applied On' },
    ];
    exportToCsv(candidatesData.data as unknown as Record<string, unknown>[], cols, 'candidates.csv');
  };

  const columns: Column<Candidate>[] = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
      render: (c) => <span className="font-medium text-on-surface">{c.name}</span>,
    },
    { key: 'college', header: 'College', sortable: true },
    { key: 'branch', header: 'Branch', sortable: true },
    {
      key: 'cgpa',
      header: 'CGPA',
      sortable: true,
      render: (c) => <span className="font-mono text-xs">{c.cgpa.toFixed(1)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (c) => (
        <Badge variant={c.display_status === 'selected' ? 'success' : c.display_status === 'rejected' ? 'danger' : 'default'}>
          {STATUS_LABELS[c.display_status as CandidateStatus] || c.status}
        </Badge>
      ),
    },
  ];

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1);
  };

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        {/* Pipeline Stats + Screening */}
        {candidatesData ? (
          <>
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
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-tertiary uppercase tracking-architectural">Applied → Passed</p>
                    <p className="text-xl font-bold text-on-surface">
                      {pipelineStats?.stats?.ROUND1_PASSED ?? '?'}
                      <span className="text-xs text-tertiary font-normal"> / {pipelineStats?.stats?.APPLIED ?? '?'}</span>
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleRunScreening}
                    disabled={runScreening.isPending}
                  >
                    <Play size={14} />
                    {runScreening.isPending ? 'Running...' : 'Run Screening'}
                  </Button>
                </div>
              </Card>
              <Card>
                <div className="text-xs text-tertiary uppercase tracking-architectural mb-1">R2 In Progress</div>
                <p className="text-xl font-bold text-on-surface">{pipelineStats?.stats?.ROUND2_IN_PROGRESS ?? 0}</p>
              </Card>
              <Card>
                <div className="text-xs text-tertiary uppercase tracking-architectural mb-1">Selected</div>
                <p className="text-xl font-bold text-on-surface">{pipelineStats?.stats?.SELECTED ?? 0}</p>
              </Card>
            </div>

            {/* Filter Toggle + Screening Filters */}
            <Card>
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 text-sm text-tertiary hover:text-on-surface transition-colors"
                >
                  <Filter size={14} />
                  Pipeline Filters
                  {showFilters ? <X size={14} /> : null}
                </button>
                {runScreening.data && (
                  <span className="text-xs text-secondary">
                    ✓ Screened: {runScreening.data.passed} passed, {runScreening.data.rejected} rejected
                  </span>
                )}
              </div>
              {showFilters && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-[var(--border-ghost)]">
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Branch Filter</label>
                    <input
                      type="text"
                      placeholder="e.g. CSE, ECE"
                      value={branchFilter}
                      onChange={e => { setBranchFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">College Filter</label>
                    <input
                      type="text"
                      placeholder="College name..."
                      value={collegeFilter}
                      onChange={e => { setCollegeFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Passed Out Year Min</label>
                    <input
                      type="number"
                      placeholder="e.g. 2020"
                      value={passedOutYearMinFilter}
                      onChange={e => { setPassedOutYearMinFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Passed Out Year Max</label>
                    <input
                      type="number"
                      placeholder="e.g. 2026"
                      value={passedOutYearMaxFilter}
                      onChange={e => { setPassedOutYearMaxFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Min CGPA Override</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      placeholder="Default 6.0"
                      value={minCgpaOverride}
                      onChange={e => setMinCgpaOverride(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Language Choice</label>
                    <input
                      type="text"
                      placeholder="e.g. python, java"
                      value={languageChoiceFilter}
                      onChange={e => { setLanguageChoiceFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">CGPA Min</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      placeholder="e.g. 6.0"
                      value={cgpaMinFilter}
                      onChange={e => { setCgpaMinFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">CGPA Max</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      placeholder="e.g. 9.0"
                      value={cgpaMaxFilter}
                      onChange={e => { setCgpaMaxFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Has Resume</label>
                    <select
                      value={hasResumeFilter}
                      onChange={e => { setHasResumeFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    >
                      <option value="">All</option>
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Has Govt ID</label>
                    <select
                      value={hasGovtIdFilter}
                      onChange={e => { setHasGovtIdFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    >
                      <option value="">All</option>
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Created After</label>
                    <input
                      type="date"
                      value={createdAfterFilter}
                      onChange={e => { setCreatedAfterFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Created Before</label>
                    <input
                      type="date"
                      value={createdBeforeFilter}
                      onChange={e => { setCreatedBeforeFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Email Verified</label>
                    <select
                      value={emailVerifiedFilter}
                      onChange={e => { setEmailVerifiedFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    >
                      <option value="">All</option>
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Phone</label>
                    <input
                      type="text"
                      placeholder="Phone number..."
                      value={phoneFilter}
                      onChange={e => { setPhoneFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Email</label>
                    <input
                      type="text"
                      placeholder="exact email..."
                      value={emailFilter}
                      onChange={e => { setEmailFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Name</label>
                    <input
                      type="text"
                      placeholder="Candidate name..."
                      value={nameFilter}
                      onChange={e => { setNameFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-tertiary mb-1">Passed Out Year (exact)</label>
                    <input
                      type="number"
                      placeholder="e.g. 2025"
                      value={passedOutYearFilter}
                      onChange={e => { setPassedOutYearFilter(e.target.value); setPage(1); }}
                      className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
                    />
                  </div>
                </div>
              )}
              {runScreening.isError && (
                <p className="text-xs text-danger mt-2">Screening failed: {(runScreening.error as Error)?.message}</p>
              )}
            </Card>
          </>
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
                <div className="flex items-center gap-2">
                  <Button variant="secondary" size="sm" onClick={handleDownloadCsv} disabled={!candidatesData?.data?.length}>
                    <Download size={14} />
                    CSV
                  </Button>
                  <Button variant="secondary" size="sm">
                    <Upload size={14} />
                    Bulk Upload
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" />
                  <input
                    type="text"
                    placeholder="Search candidates..."
                    value={search}
                    onChange={e => { setSearch(e.target.value); setPage(1); }}
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
                total_pages={candidatesData.pagination.total_pages}
                onPageChange={setPage}
                onRowClick={c => navigate(`/candidates/${c.id}`)}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSort={handleSort}
              />
            ) : null}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
