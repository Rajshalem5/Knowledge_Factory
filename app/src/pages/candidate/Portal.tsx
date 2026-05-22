import { useMyCandidateProfile, useUploadResume } from '../../hooks/useCandidates';
import { useActiveAssessments, useStartAssessment } from '../../hooks/useAssessment';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardHeader, CardTitle, Badge, ProgressPipeline, LoadingState, ErrorState, Button } from '../../components/ui';
import { STATUS_LABELS } from '../../utils/roles';
import { 
  Clock, FileText, User, 
  AlertCircle, Bell, 
  Award, Briefcase,
  GraduationCap, ClipboardCheck
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useRef } from 'react';
import type { CandidateStatus, Candidate } from '../../types';

const PIPELINE_STEPS = [
  { id: 'applied', label: 'Applied' },
  { id: 'eligible', label: 'Eligibility Review' },
  { id: 'round1', label: 'Technical MCQ' },
  { id: 'round2', label: 'Coding Assessment' },
  { id: 'interview', label: 'Interview' },
  { id: 'selected', label: 'Selected' },
];

const STATUS_INDEX: Record<string, number> = {
  'applied': 0,
  'eligible': 1,
  'round1': 2,
  'round2': 3,
  'round3': 4,
  'interviewed': 4,
  'selected': 5,
  'rejected': 5,
};

interface PortalProps {
  tab?: 'dashboard' | 'assessments' | 'profile' | 'documents' | 'results' | 'notifications';
}

export default function Portal({ tab = 'dashboard' }: PortalProps) {
  console.log('[Portal] === RENDERING === tab:', tab);
  const navigate = useNavigate();
  const { data: profile, isLoading: profileLoading, error: profileError } = useMyCandidateProfile();
  console.log('[Portal] profile:', typeof profile, profile);
  const { data: assessments } = useActiveAssessments();
  const startAssessment = useStartAssessment();
  const uploadResume = useUploadResume();
  const fileInputRef = useRef<HTMLInputElement>(null);

  console.log('[Portal] Active assessments:', assessments?.length);

  const handleStartAssessment = () => {
    const round = profile?.status === 'ROUND2_PASSED' ? 'ROUND_3' : 'ROUND_2';
    startAssessment.mutate({ round }, {
      onSuccess: () => navigate('/assessment'),
    });
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await uploadResume.mutateAsync(file);
        alert('Resume updated successfully!');
      } catch (err: any) {
        alert('Failed to upload resume: ' + err.message);
      }
    }
  };

  if (profileLoading) return <AppShell title="Candidate Portal"><LoadingState /></AppShell>;
  if (profileError) return <AppShell title="Candidate Portal"><ErrorState message="Failed to load profile" /></AppShell>;
  if (!profile) return <AppShell title="Candidate Portal"><ErrorState message="Profile not found" /></AppShell>;

  // Defensive: ensure profile has required properties
  if (!profile || typeof profile !== 'object') {
    console.error('[Portal] Invalid profile data:', profile);
    return <AppShell title="Candidate Portal"><ErrorState message="Invalid profile data" /></AppShell>;
  }

  const currentStep = STATUS_INDEX[profile.display_status] ?? 0;
  const isSelected = profile.display_status === 'selected';
  const isRejected = profile.display_status === 'rejected';

  // ── Rendering Logic ──

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <Card className="bg-primary-container text-on-primary-container border-none shadow-lg overflow-hidden relative">
        <div className="absolute right-0 top-0 h-full w-1/3 bg-white/5 skew-x-12 transform translate-x-10" />
        <div className="flex items-center gap-6 p-2">
          <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center border-2 border-white/20 overflow-hidden">
            <User size={40} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight-display">Welcome back, {profile.name}!</h1>
            <p className="text-on-primary-container/80 text-sm mt-1">
              Your application for <span className="font-semibold">Campus Hiring 2026</span> is in progress.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Progress Tracker */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base">Application Journey</CardTitle>
              <Badge variant={isSelected ? 'success' : isRejected ? 'danger' : 'warning'}>
                {STATUS_LABELS[profile.display_status as CandidateStatus] || profile.status}
              </Badge>
            </CardHeader>
            <div className="px-2 py-4">
              <ProgressPipeline steps={PIPELINE_STEPS} currentStep={currentStep} />
            </div>
          </Card>

          {/* Assessment Readiness */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ClipboardCheck size={18} className="text-secondary" />
                Assessment Readiness
              </CardTitle>
            </CardHeader>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <PortalAssessmentCard 
                title="Technical MCQ Round" 
                duration="30 Mins"
                status={getMcqStatus(profile)}
                onAction={handleStartAssessment}
                isLoading={startAssessment.isPending}
              />
              <PortalAssessmentCard 
                title="Coding Round" 
                duration="60 Mins"
                status={getCodingStatus(profile)}
                onAction={handleStartAssessment}
                isLoading={startAssessment.isPending}
              />
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Profile Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <User size={18} className="text-secondary" />
                Profile Summary
              </CardTitle>
            </CardHeader>
            <div className="space-y-4">
              <ProfileItem icon={GraduationCap} label="Degree" value={profile.degree || "Unknown"} />
              <ProfileItem icon={Briefcase} label="Branch" value={profile.branch} />
              <ProfileItem icon={Award} label="CGPA" value={`${profile.cgpa}/10.0`} />
              <ProfileItem 
                icon={FileText} 
                label="Resume" 
                value={profile.resume_url ? "Uploaded ✅" : "Missing ⚠️"} 
              />
              <div className="pt-2">
                <Button variant="ghost" size="sm" onClick={() => navigate('/portal/profile')} className="w-full justify-center">
                  View Full Profile
                </Button>
              </div>
            </div>
          </Card>

          {/* Activity Feed */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Bell size={18} className="text-secondary" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <div className="space-y-4">
              {getRecentActivity(profile).length > 0 ? (
                getRecentActivity(profile).map((act, i) => (
                  <div key={i} className="flex gap-3 items-start border-l-2 border-secondary/20 pl-3 py-1">
                    <div className="text-xs">
                      <p className="text-on-surface font-medium">{act.text}</p>
                      <p className="text-[10px] text-tertiary mt-0.5">{act.time}</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-tertiary italic text-center py-4">No recent activity</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );

  const renderAssessments = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Assessment Center</h1>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
         <DetailedPortalAssessmentCard 
            round="Round 1"
            name="Technical MCQ"
            description="Tests CS fundamentals, OS, DBMS, and OOPs concepts."
            duration="30 Minutes"
            status={getMcqStatus(profile)}
            onAction={handleStartAssessment}
            score={profile.scores.find(s => s.round === 'ROUND_2')?.score}
         />
         <DetailedPortalAssessmentCard 
            round="Round 2"
            name="Coding Assessment"
            description="Data structures and algorithmic problem solving."
            duration="60 Minutes"
            status={getCodingStatus(profile)}
            onAction={handleStartAssessment}
            score={profile.scores.find(s => s.round === 'ROUND_3')?.score}
         />
         <DetailedPortalAssessmentCard 
            round="Round 3"
            name="Technical Interview"
            description="Face-to-face interaction with technical experts."
            duration="45-60 Minutes"
            status={getInterviewStatus(profile)}
            onAction={() => {}}
         />
      </div>
    </div>
  );

  const renderResults = () => (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">My Results</h1>
      <Card>
        <div className="p-0 overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-[var(--bg-layer1)] text-tertiary uppercase text-[10px] font-bold tracking-widest">
              <tr>
                <th className="px-6 py-4">Assessment Round</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-center">Score</th>
                <th className="px-6 py-4 text-right">Completion Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant">
              {profile.scores.map((score, i) => (
                <tr key={i} className="hover:bg-secondary/5 transition-colors">
                  <td className="px-6 py-4 font-medium text-on-surface">
                    {score.round === 'ROUND_2' ? 'Technical MCQ' : 'Coding Assessment'}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Badge variant="success">Completed</Badge>
                  </td>
                  <td className="px-6 py-4 text-center font-bold text-secondary">
                    {score.score}%
                  </td>
                  <td className="px-6 py-4 text-right text-tertiary">
                    {score.completedAt ? new Date(score.completedAt).toLocaleDateString() : 'N/A'}
                  </td>
                </tr>
              ))}
              {profile.scores.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-tertiary italic">
                    No assessment results available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );

  const renderDocuments = () => (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Resume & Documents</h1>
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-secondary/10 rounded-lg text-secondary">
              <FileText size={24} />
            </div>
            <div>
              <p className="font-bold text-on-surface">Primary Resume</p>
              <p className="text-xs text-tertiary">{profile.resume_url ? `Current: ${profile.resume_url.split('/').pop()}` : "No resume uploaded"}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".pdf,.doc,.docx" 
              onChange={handleResumeUpload}
            />
            {profile.resume_url && (
              <Button variant="secondary" size="sm" onClick={() => window.open(`/${profile.resume_url}`, '_blank')}>View</Button>
            )}
            <Button size="sm" onClick={() => fileInputRef.current?.click()} isLoading={uploadResume.isPending}>
              {profile.resume_url ? 'Replace' : 'Upload'}
            </Button>
          </div>
        </div>
      </Card>
      <div className="p-4 rounded-md bg-info/10 border border-info/20 flex gap-3">
        <AlertCircle size={18} className="text-info shrink-0" />
        <p className="text-xs text-info-on-container leading-relaxed">
          Ensure your resume is up-to-date. Recruiters use this document for final selection and interview preparation.
        </p>
      </div>
    </div>
  );

  const renderProfile = () => (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">My Profile</h1>
      <Card>
        <div className="space-y-8">
           <div className="flex items-center gap-6">
              <div className="w-24 h-24 rounded-2xl bg-secondary/10 flex items-center justify-center border border-secondary/20 overflow-hidden">
                <User size={48} className="text-secondary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-on-surface">{profile.name}</h2>
                <p className="text-sm text-tertiary">{profile.email}</p>
                <div className="mt-2 flex gap-2">
                   <Badge variant="info">{profile.branch}</Badge>
                   <Badge variant="info">Batch {profile.passed_out_year}</Badge>
                </div>
              </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-tertiary">Education Details</h3>
                <div className="space-y-3">
                   <ProfileItem icon={GraduationCap} label="Degree" value={profile.degree || "Unknown"} />
                   <ProfileItem icon={Briefcase} label="Branch" value={profile.branch} />
                   <ProfileItem icon={Award} label="CGPA" value={`${profile.cgpa}/10.0`} />
                </div>
              </div>
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-tertiary">Skillset</h3>
                <div className="flex flex-wrap gap-2">
                   {profile.skills ? profile.skills.split(',').map((s, i) => (
                     <Badge key={i} variant="default">{s.trim().toUpperCase()}</Badge>
                   )) : (
                     <p className="text-xs text-tertiary italic">No skills listed</p>
                   )}
                </div>
              </div>
           </div>
        </div>
      </Card>
    </div>
  );

  const activity = getRecentActivity(profile);

  return (
    <AppShell title={tab.charAt(0).toUpperCase() + tab.slice(1)}>
      {tab === 'dashboard' && renderDashboard()}
      {tab === 'assessments' && renderAssessments()}
      {tab === 'results' && renderResults()}
      {tab === 'documents' && renderDocuments()}
      {tab === 'profile' && renderProfile()}
      {tab === 'notifications' && (
        <div className="space-y-6 max-w-2xl">
          <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Notifications</h1>
          <Card>
             <div className="space-y-6">
                {activity.length > 0 ? (
                  activity.map((act, i) => (
                    <div key={i} className="flex gap-4 p-3 rounded-md hover:bg-[var(--bg-layer1)] transition-colors group">
                      <div className="p-2 rounded bg-secondary/10 text-secondary group-hover:bg-secondary group-hover:text-white transition-colors">
                        <Bell size={16} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-on-surface">{act.text}</p>
                        <p className="text-xs text-tertiary mt-1">Official update regarding your application process.</p>
                        <p className="text-[10px] text-tertiary mt-2">{act.time}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-10">
                    <Bell size={32} className="mx-auto text-tertiary opacity-20 mb-3" />
                    <p className="text-sm text-tertiary italic">No notifications yet.</p>
                  </div>
                )}
             </div>
          </Card>
        </div>
      )}
    </AppShell>
  );
}

// ── Helper Components ──

function PortalAssessmentCard({ title, duration, status, onAction, isLoading }: any) {
  const isAvailable = status === 'Available';
  const isCompleted = status === 'Completed';
  const isInProgress = status === 'In Progress';

  return (
    <div className={`p-4 rounded-xl border transition-all ${
      isAvailable ? 'bg-secondary/5 border-secondary/20 ring-1 ring-secondary/10' : 
      isCompleted ? 'bg-success/5 border-success/20' : 
      'bg-[var(--bg-layer1)] border-outline-variant opacity-60'
    }`}>
      <div className="flex justify-between items-start mb-3">
        <h4 className="font-bold text-sm text-on-surface">{title}</h4>
        <Badge variant={isAvailable || isInProgress ? 'warning' : isCompleted ? 'success' : 'default'}>
          {status}
        </Badge>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-tertiary flex items-center gap-1">
          <Clock size={10} /> {duration}
        </span>
        {(isAvailable || isInProgress) && (
          <Button size="sm" onClick={onAction} isLoading={isLoading}>
            {isInProgress ? 'Continue' : 'Start'}
          </Button>
        )}
      </div>
    </div>
  );
}

function DetailedPortalAssessmentCard({ round, name, description, duration, status, score, onAction }: any) {
  const isLocked = status === 'Locked';
  const isCompleted = status === 'Completed';
  
  return (
    <Card className={`relative overflow-hidden ${isLocked ? 'grayscale opacity-80' : ''}`}>
      <div className="absolute top-0 left-0 w-1 h-full bg-secondary" />
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-[10px] font-bold text-secondary uppercase tracking-widest">{round}</p>
            <h3 className="text-lg font-bold text-on-surface mt-1">{name}</h3>
          </div>
          <Badge variant={isCompleted ? 'success' : isLocked ? 'default' : 'warning'}>{status}</Badge>
        </div>
        <p className="text-xs text-tertiary leading-relaxed min-h-[3rem]">
          {description}
        </p>
        <div className="flex items-center gap-4 py-2 border-y border-outline-variant">
           <div>
             <p className="text-[10px] text-tertiary uppercase">Duration</p>
             <p className="text-xs font-bold text-on-surface">{duration}</p>
           </div>
           {score !== undefined && (
              <div>
                <p className="text-[10px] text-tertiary uppercase">Your Score</p>
                <p className="text-xs font-bold text-secondary">{score}%</p>
              </div>
           )}
        </div>
        <div className="pt-2">
          <Button 
            className="w-full justify-center" 
            disabled={isLocked || isCompleted}
            onClick={onAction}
          >
            {isCompleted ? 'Round Completed' : isLocked ? 'Round Locked' : 'Start Assessment'}
          </Button>
        </div>
      </div>
    </Card>
  );
}

function ProfileItem({ icon: Icon, label, value }: any) {
  return (
    <div className="flex items-center gap-3">
      <div className="p-2 bg-[var(--bg-layer2)] rounded text-tertiary">
        <Icon size={14} />
      </div>
      <div>
        <p className="text-[10px] text-tertiary uppercase tracking-architectural">{label}</p>
        <p className="text-sm font-medium text-on-surface">{value}</p>
      </div>
    </div>
  );
}

// ── State Helper Functions ──

function getMcqStatus(profile: Candidate) {
  if (profile.status === 'ROUND1_PASSED') return 'Available';
  if (profile.status === 'ROUND2_IN_PROGRESS') return 'In Progress';
  if (['ROUND2_PASSED', 'ROUND2_REJECTED', 'ROUND3_IN_PROGRESS', 'ROUND3_PASSED', 'INTERVIEW_SCHEDULED', 'SELECTED'].includes(profile.status)) {
    return 'Completed';
  }
  return 'Locked';
}

function getCodingStatus(profile: Candidate) {
  if (profile.status === 'ROUND2_PASSED') return 'Available';
  if (profile.status === 'ROUND3_IN_PROGRESS') return 'In Progress';
  if (['ROUND3_PASSED', 'INTERVIEW_SCHEDULED', 'SELECTED'].includes(profile.status)) {
    return 'Completed';
  }
  return 'Locked';
}

function getInterviewStatus(profile: Candidate) {
  if (profile.status === 'ROUND3_PASSED') return 'Pending';
  if (profile.status === 'INTERVIEW_SCHEDULED') return 'Scheduled';
  if (['INTERVIEW_COMPLETED', 'SELECTED'].includes(profile.status)) return 'Completed';
  return 'Locked';
}

function getRecentActivity(profile: Candidate) {
  const activities = [
    { text: "Application submitted successfully", time: "Just now" }
  ];
  if (profile.status !== 'APPLIED') {
    activities.unshift({ text: "Eligibility criteria approved", time: "1 day ago" });
  }
  if (profile.scores.some(s => s.round === 'ROUND_2')) {
    activities.unshift({ text: "Technical MCQ Round completed", time: "Recently" });
  }
  if (profile.status === 'ROUND2_PASSED') {
    activities.unshift({ text: "Coding Assessment Round unlocked", time: "Recently" });
  }
  if (profile.status === 'SELECTED') {
    activities.unshift({ text: "Congratulations! You have been selected.", time: "Recently" });
  }
  return activities;
}
