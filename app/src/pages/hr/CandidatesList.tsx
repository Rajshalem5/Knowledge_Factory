import { useState, useEffect } from 'react';
// TODO: Re-enable CandidateDetail after type and hook issues are resolved
// import { useNavigate } from 'react-router-dom';
import { Search, Filter, X, Download, FileText, FileX, Phone, PhoneOff } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Button, Select, Badge, LoadingState, ErrorState } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { useCandidates } from '../../hooks/useCandidates';
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

export default function CandidatesList() {
  // const navigate = useNavigate(); // TODO: Re-enable when CandidateDetail is restored
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [cgpaMinFilter, setCgpaMinFilter] = useState('');
  const [passedOutYearFilter, setPassedOutYearFilter] = useState('');
  const [languageChoiceFilter, setLanguageChoiceFilter] = useState('');
  
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { data: candidatesData, isLoading, error } = useCandidates({
    page,
    limit: 15,
    search: search || undefined,
    status: statusFilter || undefined,
    branch: branchFilter || undefined,
    cgpa_min: cgpaMinFilter ? parseFloat(cgpaMinFilter) : undefined,
    passed_out_year: passedOutYearFilter ? parseInt(passedOutYearFilter, 10) : undefined,
    language_choice: languageChoiceFilter || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  useEffect(() => {
    console.log('[CandidatesList] candidatesData response:', candidatesData);
  }, [candidatesData]);

  // Defensive normalization
  const candidates = Array.isArray(candidatesData?.data) ? candidatesData.data : [];
  const totalItems = candidatesData?.pagination?.total ?? 0;
  const totalPages = candidatesData?.pagination?.total_pages ?? 1;

  const handleDownloadCsv = () => {
    if (!candidates.length) return;
    const cols = [
      { key: 'name', header: 'Name' },
      { key: 'email', header: 'Email' },
      { key: 'phone', header: 'Phone' },
      { key: 'college', header: 'College' },
      { key: 'branch', header: 'Branch' },
      { key: 'cgpa', header: 'CGPA' },
      { key: 'passed_out_year', header: 'Passed Out Year' },
      { key: 'language_choice', header: 'Language' },
      { key: 'display_status', header: 'Status' },
      { key: 'created_at', header: 'Applied On' },
    ];
    exportToCsv(candidates as unknown as Record<string, unknown>[], cols, 'candidates_export.csv');
  };

  const columns: Column<Candidate>[] = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
      render: (c) => (
        <div>
           <p className="font-medium text-on-surface">{c.name}</p>
           <p className="text-[10px] text-tertiary">{c.email}</p>
        </div>
      ),
    },
    { key: 'degree', header: 'Degree', sortable: true },
    { key: 'college', header: 'College', sortable: true },
    { key: 'branch', header: 'Branch', sortable: true },
    {
      key: 'resume_url',
      header: 'Docs',
      sortable: false,
      render: (c) => (
        <div className="flex items-center gap-1.5">
          {c.resume_url ? (
            <span className="text-secondary" title="Resume uploaded">
              <FileText size={14} />
            </span>
          ) : (
            <span className="text-danger/30" title="No resume">
              <FileX size={14} />
            </span>
          )}
          {c.phone ? (
            <span className="text-secondary" title={`Phone: ${c.phone}`}>
              <Phone size={14} />
            </span>
          ) : (
            <span className="text-danger/30" title="No phone">
              <PhoneOff size={14} />
            </span>
          )}
        </div>
      ),
    },
    { key: 'passed_out_year', header: 'Batch', sortable: true },
    {
      key: 'cgpa',
      header: 'CGPA',
      sortable: true,
      render: (c) => <span className="font-mono text-xs">{c.cgpa.toFixed(1)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
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
    <AppShell title="Candidate Management">
      <div className="space-y-6">
        {/* Header & Main Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div>
             <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Candidates</h1>
             <p className="text-sm text-tertiary">Total records found: {totalItems}</p>
           </div>
           <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={handleDownloadCsv} disabled={!candidates.length}>
                <Download size={14} />
                Export CSV
              </Button>
           </div>
        </div>

        {/* Filter Card */}
        <Card>
          <div className="flex flex-col md:flex-row md:items-center gap-4 mb-4">
            <div className="flex-1 relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" />
              <input
                type="text"
                placeholder="Search candidates by name, email, or college..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="w-full pl-9 pr-3 py-2 rounded-md bg-[var(--bg-base)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50 border border-[var(--border-ghost)]"
              />
            </div>
            <Select
              options={STATUS_OPTIONS}
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
              className="w-full md:w-48"
            />
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowFilters(!showFilters)}
              className={showFilters ? 'bg-secondary/10 text-secondary' : ''}
            >
              <Filter size={14} />
              {showFilters ? 'Hide Advanced' : 'Advanced Filters'}
            </Button>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-[var(--border-ghost)]">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1.5">Branch</label>
                <input
                  type="text"
                  placeholder="e.g. CSE, ECE"
                  value={branchFilter}
                  onChange={e => { setBranchFilter(e.target.value); setPage(1); }}
                  className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface focus:outline-none border border-[var(--border-ghost)]"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1.5">CGPA Min</label>
                <input
                  type="number"
                  step="0.1"
                  value={cgpaMinFilter}
                  onChange={e => { setCgpaMinFilter(e.target.value); setPage(1); }}
                  className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface focus:outline-none border border-[var(--border-ghost)]"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1.5">Batch Year</label>
                <input
                  type="number"
                  value={passedOutYearFilter}
                  onChange={e => { setPassedOutYearFilter(e.target.value); setPage(1); }}
                  className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface focus:outline-none border border-[var(--border-ghost)]"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1.5">Language</label>
                <input
                  type="text"
                  placeholder="python, java..."
                  value={languageChoiceFilter}
                  onChange={e => { setLanguageChoiceFilter(e.target.value); setPage(1); }}
                  className="w-full px-3 py-1.5 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface focus:outline-none border border-[var(--border-ghost)]"
                />
              </div>
              <div className="sm:col-span-2 lg:col-span-4 flex justify-end">
                 <button 
                   onClick={() => {
                     setBranchFilter(''); setCgpaMinFilter(''); setPassedOutYearFilter(''); 
                     setLanguageChoiceFilter(''); setSearch(''); setStatusFilter('');
                     setPage(1);
                   }}
                   className="text-xs text-danger hover:underline flex items-center gap-1"
                 >
                   <X size={12} /> Clear all
                 </button>
              </div>
            </div>
          )}
        </Card>

        {/* Table Results */}
        <Card padding="none">
          {isLoading ? (
            <LoadingState />
          ) : error ? (
            <ErrorState message="Failed to load candidates" />
          ) : (
            <DataTable
              columns={columns}
              data={candidates}
              keyExtractor={c => c.id}
              page={page}
              total_pages={totalPages}
              onPageChange={setPage}
              // TODO: Re-enable CandidateDetail after type and hook issues are resolved
              // onRowClick={c => navigate(`/candidates/${c.id}`)}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSort={handleSort}
            />
          )}
        </Card>
      </div>
    </AppShell>
  );
}
