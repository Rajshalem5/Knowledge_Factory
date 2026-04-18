import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, LoadingState, ErrorState } from '../../components/ui';
import { StatCard } from '../../components/charts/StatCard';
import { BarChart } from '../../components/charts/BarChart';
import { FunnelChart } from '../../components/charts/FunnelChart';
import { useAnalytics, useFunnelData } from '../../hooks/useAnalytics';
import { BarChart3, Users, AlertTriangle, TrendingUp } from 'lucide-react';

export default function AnalyticsDashboard() {
  const { data: analytics, isLoading, error } = useAnalytics();
  const { data: funnelData } = useFunnelData();

  if (isLoading) return <AppShell title="Analytics"><LoadingState /></AppShell>;
  if (error) return <AppShell title="Analytics"><ErrorState message="Failed to load analytics" /></AppShell>;

  const sampleAnalytics = {
    passRatePerRound: [
      { round: 'Round 1', passRate: 72 },
      { round: 'Round 2', passRate: 58 },
      { round: 'Round 3', passRate: 41 },
      { round: 'Interview', passRate: 65 },
    ],
    collegeBreakdown: [
      { college: 'IIT Delhi', count: 145, avgScore: 78 },
      { college: 'NIT Trichy', count: 132, avgScore: 74 },
      { college: 'BITS Pilani', count: 98, avgScore: 76 },
      { college: 'VIT Vellore', count: 87, avgScore: 68 },
      { college: 'DTU', count: 76, avgScore: 71 },
    ],
    branchPerformance: [
      { branch: 'Computer Science', count: 234, avgScore: 79 },
      { branch: 'Information Tech', count: 178, avgScore: 73 },
      { branch: 'Electronics', count: 145, avgScore: 67 },
      { branch: 'Electrical', count: 89, avgScore: 62 },
      { branch: 'Mechanical', count: 45, avgScore: 58 },
    ],
    proctoringViolations: [
      { type: 'Tab Switch', count: 234 },
      { type: 'Face Not Detected', count: 89 },
      { type: 'Multiple Faces', count: 23 },
      { type: 'Copy Paste', count: 156 },
    ],
  };

  const data = analytics ?? sampleAnalytics;

  return (
    <AppShell title="Analytics">
      <div className="space-y-6">
        {/* Overview stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Candidates" value="1,240" change={{ value: 12, positive: true }} icon={Users} />
          <StatCard label="Overall Pass Rate" value="64%" change={{ value: 5, positive: true }} icon={TrendingUp} />
          <StatCard label="Avg Score" value="71.4" change={{ value: 3, positive: true }} icon={BarChart3} />
          <StatCard label="Violations" value="502" change={{ value: 8, positive: false }} icon={AlertTriangle} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pass Rate Per Round */}
          <Card>
            <CardHeader>
              <CardTitle>Pass Rate Per Round</CardTitle>
            </CardHeader>
            <BarChart
              data={data.passRatePerRound.map(r => ({ label: r.round, value: r.passRate }))}
              maxValue={100}
            />
          </Card>

          {/* Funnel */}
          <Card>
            <CardHeader>
              <CardTitle>Hiring Funnel</CardTitle>
            </CardHeader>
            {funnelData ? (
              <FunnelChart data={funnelData} />
            ) : (
              <FunnelChart data={{ applied: 1240, eligible: 890, assessed: 645, interviewed: 280, selected: 95 }} />
            )}
          </Card>

          {/* College Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>College-wise Breakdown</CardTitle>
            </CardHeader>
            <BarChart
              data={data.collegeBreakdown.map(c => ({ label: c.college, value: c.count }))}
            />
          </Card>

          {/* Branch Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Branch-wise Performance</CardTitle>
            </CardHeader>
            <BarChart
              data={data.branchPerformance.map(b => ({ label: b.branch, value: b.avgScore }))}
              maxValue={100}
            />
          </Card>

          {/* Proctoring Violations */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Proctoring Violations</CardTitle>
            </CardHeader>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {data.proctoringViolations.map(v => (
                <div key={v.type} className="p-4 rounded-md bg-[var(--bg-layer1)] text-center">
                  <p className="text-2xl font-bold text-danger">{v.count}</p>
                  <p className="text-xs text-tertiary uppercase tracking-architectural mt-1">{v.type}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
