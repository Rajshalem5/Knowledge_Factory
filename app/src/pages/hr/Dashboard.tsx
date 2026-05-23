import { useNavigate } from 'react-router-dom';
import { Users, Upload, Play, CheckCircle, Database, History, ArrowRight } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Button, LoadingState, ErrorState } from '../../components/ui';
import { FunnelChart } from '../../components/charts/FunnelChart';
import { useFunnelData } from '../../hooks/useAnalytics';
import { useRunScreening, usePipelineStats } from '../../hooks/useScreening';
import { useAuth } from '../../contexts/AuthContext';
import { UserManagement } from '../../components/admin/UserManagement';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data: funnelData, isLoading: funnelLoading } = useFunnelData();
  const { data: pipelineStats } = usePipelineStats();
  const runScreening = useRunScreening();

  const handleRunScreening = () => {
    runScreening.mutate(undefined);
  };

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div>
             <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Recruitment Overview</h1>
             <p className="text-sm text-tertiary">Real-time pipeline health and metrics</p>
           </div>
           <div className="flex items-center gap-2">
              <Button size="sm" onClick={() => navigate('/uploads')}>
                <Upload size={14} />
                Bulk Upload
              </Button>
           </div>
        </div>

        {/* Pipeline Aggregates */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
           <StatCard label="Total Applied" value={pipelineStats?.aggregates?.total_filtered ?? 0} icon={Users} color="secondary" />
           <StatCard label="Eligible (R1)" value={pipelineStats?.stats?.ROUND1_PASSED ?? 0} icon={CheckCircle} color="success" />
           <StatCard label="In Assessment" value={(pipelineStats?.stats?.ROUND2_IN_PROGRESS ?? 0) + (pipelineStats?.stats?.ROUND3_IN_PROGRESS ?? 0)} icon={Play} color="warning" />
           <StatCard label="Selected" value={pipelineStats?.stats?.SELECTED ?? 0} icon={Database} color="secondary" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Funnel */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Hiring Funnel</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/analytics')}>Details</Button>
            </CardHeader>
            <div className="h-[350px] flex items-center justify-center">
              {funnelLoading ? (
                <LoadingState message="Calculating funnel..." />
              ) : funnelData ? (
                <FunnelChart data={funnelData} />
              ) : (
                <ErrorState message="Funnel data unavailable" />
              )}
            </div>
          </Card>

          {/* Action Center */}
          <div className="space-y-6">
             <Card>
                <CardHeader>
                   <CardTitle className="text-sm">Action Center</CardTitle>
                </CardHeader>
                <div className="space-y-3">
                   <div className="p-3 rounded-lg bg-[var(--bg-layer1)] border border-outline-variant flex items-center justify-between">
                      <div>
                         <p className="text-xs font-bold text-on-surface">Eligibility Screening</p>
                         <p className="text-[10px] text-tertiary">Run Round 1 auto-filters</p>
                      </div>
                      <Button size="sm" onClick={handleRunScreening} isLoading={runScreening.isPending}>
                         Run
                      </Button>
                   </div>
                   <div className="p-3 rounded-lg bg-[var(--bg-layer1)] border border-outline-variant flex items-center justify-between">
                      <div>
                         <p className="text-xs font-bold text-on-surface">Manage Candidates</p>
                         <p className="text-[10px] text-tertiary">Full list and filters</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => navigate('/candidates')}>
                         <ArrowRight size={14} />
                      </Button>
                   </div>
                </div>
             </Card>

             <Card>
                <CardHeader>
                   <CardTitle className="text-sm flex items-center gap-2">
                      <History size={14} className="text-secondary" />
                      Recent Ingestions
                   </CardTitle>
                </CardHeader>
                <div className="space-y-4">
                   {pipelineStats?.aggregates?.total_filtered ? (
                      <div className="flex items-start gap-3">
                         <div className="p-1.5 rounded bg-secondary/10 text-secondary mt-0.5">
                            <Upload size={12} />
                         </div>
                         <div>
                            <p className="text-xs font-medium text-on-surface truncate">Database Records</p>
                            <p className="text-[10px] text-tertiary">{pipelineStats.aggregates.total_filtered} total candidates in pipeline</p>
                         </div>
                      </div>
                   ) : (
                      <p className="text-[10px] text-tertiary italic text-center py-2">No recent activity</p>
                   )}
                   <Button variant="ghost" size="sm" className="w-full justify-center" onClick={() => navigate('/uploads')}>
                      View History
                   </Button>
                </div>
             </Card>
          </div>
        </div>

        {/* User Management Section (for Admins) */}
        {(user?.role === 'admin' || user?.role === 'superadmin') && (
          <div className="mt-8">
             <CardHeader className="px-0">
                <CardTitle className="text-xl">User Management</CardTitle>
             </CardHeader>
             <UserManagement manageAdmins={user.role === 'superadmin'} />
          </div>
        )}
      </div>
    </AppShell>
  );
}

function StatCard({ label, value, icon: Icon, color }: any) {
  const colorMap: any = {
    secondary: 'bg-secondary/10 text-secondary',
    success: 'bg-success/10 text-success',
    warning: 'bg-warning/10 text-warning',
    info: 'bg-info/10 text-info',
  };

  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-md ${colorMap[color] || colorMap.secondary}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-[10px] text-tertiary uppercase tracking-architectural font-bold">{label}</p>
          <p className="text-2xl font-bold text-on-surface tracking-tight-display leading-tight">{value}</p>
        </div>
      </div>
    </Card>
  );
}
