import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, LoadingState, ErrorState } from '../../components/ui';
import { BarChart } from '../../components/charts/BarChart';
import { FunnelChart } from '../../components/charts/FunnelChart';
import { useAnalytics, useFunnelData } from '../../hooks/useAnalytics';
import { Users } from 'lucide-react';

export default function AnalyticsDashboard() {
  const { data: analytics, isLoading, error } = useAnalytics();
  const { data: funnelData, isLoading: funnelLoading } = useFunnelData();

  return (
    <AppShell title="Analytics">
      <div className="space-y-6">
        {isLoading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message="Failed to load analytics" />
        ) : analytics ? (
          <>
            {/* Overview stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <div className="flex items-center gap-3">
                  <Users size={18} className="text-secondary" />
                  <div>
                    <p className="text-xs text-tertiary uppercase tracking-architectural">Total Candidates</p>
                    <p className="text-lg font-bold text-on-surface">1,240</p>
                  </div>
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pass Rate Per Round */}
              <Card>
                <CardHeader>
                  <CardTitle>Pass Rate Per Round</CardTitle>
                </CardHeader>
                <BarChart
                  data={analytics?.passRatePerRound?.map(r => ({ label: r.round, value: r.passRate })) || []}
                  maxValue={100}
                />
              </Card>

              {/* Funnel */}
              <Card>
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

              {/* College Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>College-wise Breakdown</CardTitle>
                </CardHeader>
                <BarChart
                  data={analytics?.collegeBreakdown?.map(c => ({ label: c.college, value: c.count })) || []}
                />
              </Card>

              {/* Branch Performance */}
              <Card>
                <CardHeader>
                  <CardTitle>Branch-wise Performance</CardTitle>
                </CardHeader>
                <BarChart
                  data={analytics?.branchPerformance?.map(b => ({ label: b.branch, value: b.avgScore })) || []}
                  maxValue={100}
                />
              </Card>

              {/* Proctoring Violations */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Proctoring Violations</CardTitle>
                </CardHeader>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {analytics?.proctoringViolations?.map(v => (
                    <div key={v.type} className="p-4 rounded-md bg-[var(--bg-layer1)] text-center">
                      <p className="text-2xl font-bold text-danger">{v.count}</p>
                      <p className="text-xs text-tertiary uppercase tracking-architectural mt-1">{v.type}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
