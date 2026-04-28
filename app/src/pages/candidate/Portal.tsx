import { AppShell } from '../../components/layout/AppShell';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  Badge, 
  ProgressPipeline, 
  LoadingState, 
  ErrorState,
  Button
} from '../../components/ui';
import { useMyCandidateProfile } from '../../hooks/useCandidates';
import { useActiveAssessments } from '../../hooks/useAssessment';
import { STATUS_LABELS } from '../../utils/roles';
import { 
  Clock, 
  FileText, 
  Trophy, 
  ArrowRight,
  User,
  GraduationCap,
  Award,
  Calendar,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { CandidateStatus } from '../../types';
import { cn } from '../../utils/cn';

const PIPELINE_STEPS = [
  { id: 'applied', label: 'Application' },
  { id: 'eligible', label: 'Eligible' },
  { id: 'round1', label: 'Round 1' },
  { id: 'round2', label: 'Round 2' },
  { id: 'round3', label: 'Round 3' },
  { id: 'interview', label: 'Interview' },
];

const STATUS_INDEX: Record<CandidateStatus, number> = {
  applied: 0,
  eligible: 1,
  round1: 2,
  round2: 3,
  round3: 4,
  interviewed: 5,
  selected: 6,
  rejected: 5,
};

// Mock data for demonstration
const MOCK_PROFILE = {
  name: "Alex Johnson",
  email: "alex.johnson@example.com",
  college: "University of Technology",
  branch: "Computer Science",
  cgpa: "8.7/10",
  status: "round1" as CandidateStatus,
  scores: [
    { round: 1, score: 15, maxScore: 20 },
    { round: 2, score: 18, maxScore: 20 }
  ]
};

const MOCK_ASSESSMENTS = [
  { id: 'a1', round: 1, status: 'in_progress', timeLimit: 90 },
  { id: 'a2', round: 2, status: 'available', timeLimit: 120 },
];

export default function Portal() {
  const navigate = useNavigate();
  
  // Using mock data as placeholder without backend connection
  const profileLoading = false;
  const profileError = null;
  const profile = MOCK_PROFILE;
  const assessments = MOCK_ASSESSMENTS;

  if (profileLoading) return <AppShell title="My Portal"><LoadingState /></AppShell>;
  if (profileError) return <AppShell title="My Portal"><ErrorState message="Failed to load profile" /></AppShell>;
  if (!profile) return <AppShell title="My Portal"><ErrorState message="Profile not found" /></AppShell>;

  const currentStep = STATUS_INDEX[profile.status] ?? 0;
  const isSelected = profile.status === 'selected';
  const isRejected = profile.status === 'rejected';

  return (
    <AppShell title="My Portal">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="mb-10">
          <h1 className="text-3xl md:text-4xl font-bold text-on-surface mb-2">Welcome Back, {profile.name}!</h1>
          <p className="text-lg text-on-surface-variant">Track your application progress and preparation</p>
        </div>

        {/* Profile Overview */}
        <Card className="mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between p-6">
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-secondary to-primary flex items-center justify-center">
                <User size={32} className="text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-on-surface">{profile.name}</h2>
                <p className="text-on-surface-variant">{profile.email}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge variant="default" className="flex items-center gap-1">
                    <GraduationCap size={14} />
                    {profile.college}
                  </Badge>
                  <Badge variant="default" className="flex items-center gap-1">
                    <Award size={14} />
                    {profile.branch}
                  </Badge>
                  <Badge variant="default" className="flex items-center gap-1">
                    <Trophy size={14} />
                    CGPA: {profile.cgpa}
                  </Badge>
                </div>
              </div>
            </div>
            <Badge 
              variant={isSelected ? 'success' : isRejected ? 'danger' : 'info'} 
              className="self-start md:self-auto"
            >
              <span className="flex items-center gap-1">
                {isSelected ? <CheckCircle size={16} /> : isRejected ? <XCircle size={16} /> : null}
                {STATUS_LABELS[profile.status]}
              </span>
            </Badge>
          </div>
        </Card>

        {/* Application Progress */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Application Progress</CardTitle>
          </CardHeader>
          <div className="p-6">
            <div className="mb-4">
              <ProgressPipeline 
                steps={PIPELINE_STEPS} 
                currentStep={currentStep} 
                className="pb-4"
              />
            </div>
            
            {isSelected || isRejected ? (
              <div className={cn(
                "p-4 rounded-lg flex items-center gap-3",
                isSelected 
                  ? "bg-success/10 text-success border border-success/20" 
                  : "bg-danger/10 text-danger border border-danger/20"
              )}>
                {isSelected ? (
                  <CheckCircle size={20} />
                ) : (
                  <XCircle size={20} />
                )}
                <p className="font-medium">
                  {isSelected 
                    ? "Congratulations! You've been selected!" 
                    : "Sorry, your application wasn't selected this time."}
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/10">
                <div className="flex items-center gap-3 mb-2">
                  <Calendar size={16} className="text-primary" />
                  <p className="font-medium text-primary">{STATUS_LABELS[profile.status]}</p>
                </div>
                <p className="text-sm text-on-surface-variant">
                  {profile.status === 'applied' && 'Your application is being reviewed for eligibility. Check back soon for updates!'}
                  {profile.status === 'eligible' && 'You are eligible! Wait for Round 1 assessment to begin, or check the Active Assessments section below.'}
                  {profile.status === 'round1' && 'Round 1 assessment is available. Start by clicking "Take Assessment" below.'}
                  {profile.status === 'round2' && 'You passed Round 1! Round 2 assessment is ready. Prepare for the next challenge.'}
                  {profile.status === 'round3' && 'Great progress! Complete Round 3 to advance further in the process.'}
                  {profile.status === 'interviewed' && 'Interview complete. Results will be announced soon. Stay tuned!'}
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Active Assessments */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Active Assessments</CardTitle>
          </CardHeader>
          <div className="p-6">
            {assessments && assessments.length > 0 ? (
              <div className="space-y-4">
                {assessments.map((a) => (
                  <div key={a.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-surface-container-low border border-outline-variant/20 hover:shadow-sm transition-shadow duration-200">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-secondary/10">
                        <FileText size={20} className="text-secondary" />
                      </div>
                      <div className="flex-1">
                        <p className="text-lg font-semibold text-on-surface">Round {a.round} Assessment</p>
                        <p className="text-sm text-on-surface-variant mt-1">
                          <Clock size={14} className="inline mr-1" />
                          {a.timeLimit} minutes • {a.status === 'in_progress' ? 'In Progress' : 'Ready to Start'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={a.status === 'in_progress' ? 'info' : 'default'}>
                        {a.status === 'in_progress' ? 'In Progress' : 'Available'}
                      </Badge>
                      <Button
                        variant={a.status === 'in_progress' ? 'primary' : 'secondary'}
                        onClick={() => navigate('/assessment')}
                        disabled={a.status === 'completed'}
                        className="flex items-center gap-2"
                      >
                        {a.status === 'in_progress' ? (
                          <>
                            <ArrowRight size={16} />
                            Continue
                          </>
                        ) : (
                          <>
                            <ArrowRight size={16} />
                            Start
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-on-surface-variant">
                <FileText size={32} className="mx-auto mb-2 text-on-surface-variant/50" />
                <p>No active assessments at the moment</p>
                <p className="text-sm mt-1">Check back later for new opportunities</p>
              </div>
            )}
          </div>
        </Card>

        {/* Past Results */}
        {profile.scores.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Past Results</CardTitle>
            </CardHeader>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {profile.scores.map((score) => (
                  <div key={score.round} className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/20">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-medium text-on-surface">Round {score.round}</h3>
                      <div className="p-2 rounded-full bg-secondary/10">
                        <Trophy size={16} className="text-secondary" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-on-surface-variant">Score</span>
                        <span className="font-medium text-on-surface">{score.score}/{score.maxScore}</span>
                      </div>
                      <div className="w-full bg-surface-variant rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-secondary to-primary h-2 rounded-full transition-all duration-500"
                          style={{ width: `${(score.score / score.maxScore) * 100}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-on-surface-variant">Percentage</span>
                        <span className="font-medium text-on-surface">
                          {Math.round((score.score / score.maxScore) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-all duration-200 border-0 bg-gradient-to-br from-primary/5 to-secondary/5">
            <div className="p-5">
              <h3 className="font-semibold text-on-surface mb-2">Prepare for Next Step</h3>
              <p className="text-sm text-on-surface-variant mb-4">
                Review the concepts and practices required for Round 2.
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Study Resources
              </Button>
            </div>
          </Card>
          <Card className="hover:shadow-lg transition-all duration-200 border-0 bg-gradient-to-br from-secondary/5 to-primary/5">
            <div className="p-5">
              <h3 className="font-semibold text-on-surface mb-2">Contact Support</h3>
              <p className="text-sm text-on-surface-variant mb-4">
                Have questions? Reach out to our support team.
              </p>
              <Button variant="secondary" size="sm" className="w-full">
                Contact Us
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
