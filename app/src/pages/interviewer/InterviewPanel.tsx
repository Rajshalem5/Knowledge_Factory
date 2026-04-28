import { useMemo, useState } from 'react';
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock3,
  ExternalLink,
  FileText,
  Filter,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  Search,
  UserPlus,
  Users,
  Video,
  XCircle,
} from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Badge, Button, Card, ErrorState, LoadingState, Modal } from '../../components/ui';
import { useSubmitFeedback } from '../../hooks/useAssessment';
import { useAssignInterview, useFinalReviewCandidates, useMyInterviewAssignments } from '../../hooks/useInterviews';
import type { Candidate, InterviewAssignment } from '../../types';
import { cn } from '../../utils/cn';

type InterviewStage = 'scheduled' | 'inProgress' | 'completed';

interface InterviewItem {
  id: string;
  assignmentId: string;
  candidate: Candidate;
  role: string;
  round: string;
  stage: InterviewStage;
  dateLabel: string;
  timeLabel: string;
  meetingLink: string;
  interviewer: string;
}

const stageMeta: Record<InterviewStage, { title: string; empty: string }> = {
  scheduled: {
    title: 'Scheduled',
    empty: 'Add scheduled interviews here',
  },
  inProgress: {
    title: 'In Progress',
    empty: 'Live interviews will appear here',
  },
  completed: {
    title: 'Completed',
    empty: 'Finished interviews will appear here',
  },
};

const interviewers = [
  { id: 'marcus', name: 'Marcus Lee', specialty: 'Technical' },
  { id: 'elena', name: 'Elena Rao', specialty: 'System Design' },
  { id: 'david', name: 'David Kim', specialty: 'Culture Fit' },
];

function initials(name: string) {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function toInterviewStage(status: InterviewAssignment['status']): InterviewStage {
  if (status === 'in_progress') return 'inProgress';
  if (status === 'completed') return 'completed';
  return 'scheduled';
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { dateLabel: 'Scheduled', timeLabel: value || 'Time pending' };
  }

  return {
    dateLabel: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    timeLabel: date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }),
  };
}

function buildInterviewItems(assignments: InterviewAssignment[]): InterviewItem[] {
  return assignments.map(assignment => {
    const { candidate } = assignment;
    const { dateLabel, timeLabel } = formatDateTime(assignment.scheduledAt);

    return {
      id: `interview-${assignment.id}`,
      assignmentId: assignment.id,
      candidate,
      role: candidate.branch || 'Candidate',
      round: assignment.round || 'Technical Interview',
      stage: toInterviewStage(assignment.status),
      dateLabel,
      timeLabel,
      meetingLink: assignment.meetingLink || '',
      interviewer: assignment.interviewerName || 'Assigned Interviewer',
    };
  });
}

export default function InterviewPanel() {
  const { data: assignmentsData, isLoading, error } = useMyInterviewAssignments();
  const { data: finalReviewCandidatesData } = useFinalReviewCandidates();
  const assignInterview = useAssignInterview();
  const submitFeedback = useSubmitFeedback();
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<InterviewStage | 'all'>('all');
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [selectedInterviewId, setSelectedInterviewId] = useState<string | null>(null);
  const [candidateSearch, setCandidateSearch] = useState('');
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedInterviewer, setSelectedInterviewer] = useState(interviewers[0].id);
  const [scheduledDate, setScheduledDate] = useState('2026-04-29');
  const [scheduledTime, setScheduledTime] = useState('14:30');
  const [technicalScore, setTechnicalScore] = useState(8);
  const [communicationScore, setCommunicationScore] = useState(8);
  const [cultureScore, setCultureScore] = useState(7);
  const [notes, setNotes] = useState('');
  const [meetingLink, setMeetingLink] = useState('https://meet.google.com/abc-defg-hij');

  const assignments = useMemo(() => assignmentsData ?? [], [assignmentsData]);
  const finalReviewCandidates = useMemo(() => finalReviewCandidatesData ?? [], [finalReviewCandidatesData]);
  const interviews = useMemo(() => buildInterviewItems(assignments), [assignments]);
  const selectedInterview = interviews.find(interview => interview.id === selectedInterviewId);

  const filteredInterviews = interviews.filter(interview => {
    const text = `${interview.candidate.name} ${interview.role} ${interview.round} ${interview.interviewer}`.toLowerCase();
    const matchesQuery = text.includes(query.toLowerCase());
    const matchesFilter = activeFilter === 'all' || interview.stage === activeFilter;
    return matchesQuery && matchesFilter;
  });

  const scheduleCandidates = finalReviewCandidates.filter(candidate =>
    `${candidate.name} ${candidate.email} ${candidate.branch}`.toLowerCase().includes(candidateSearch.toLowerCase()),
  );

  const scoreCards = selectedInterview?.candidate.scores.length
    ? selectedInterview.candidate.scores.slice(0, 3)
    : [
        { round: 1, score: 85, maxScore: 100, completedAt: '' },
        { round: 2, score: 70, maxScore: 100, completedAt: '' },
      ];

  const submitDecision = (recommendation: 'select' | 'reject') => {
    if (!selectedInterview) return;

    submitFeedback.mutate({
      candidateId: selectedInterview.candidate.id,
      data: {
        interviewId: selectedInterview.assignmentId,
        candidateId: selectedInterview.candidate.id,
        technicalScore,
        communicationScore,
        culturalFitScore: cultureScore,
        recommendation,
        notes,
      },
    });
  };

  const handleScheduleInterview = () => {
    if (!selectedCandidateId) return;

    assignInterview.mutate(
      {
        candidateId: selectedCandidateId,
        interviewerId: selectedInterviewer,
        scheduledAt: new Date(`${scheduledDate}T${scheduledTime}`).toISOString(),
        meetingLink,
        round: 'Technical Interview',
      },
      {
        onSuccess: () => {
          setScheduleOpen(false);
          setCandidateSearch('');
          setSelectedCandidateId('');
        },
      },
    );
  };

  if (isLoading) {
    return (
      <AppShell title="Interviews">
        <LoadingState />
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell title="Interviews">
        <ErrorState message="Failed to load interviews" />
      </AppShell>
    );
  }

  return (
    <AppShell title="Interviews">
      {selectedInterview ? (
        <EvaluationView
          interview={selectedInterview}
          scoreCards={scoreCards}
          technicalScore={technicalScore}
          communicationScore={communicationScore}
          cultureScore={cultureScore}
          notes={notes}
          isSubmitting={submitFeedback.isPending}
          onBack={() => setSelectedInterviewId(null)}
          onTechnicalScore={setTechnicalScore}
          onCommunicationScore={setCommunicationScore}
          onCultureScore={setCultureScore}
          onNotes={setNotes}
          onSubmit={submitDecision}
        />
      ) : (
        <div className="space-y-7">
          <section className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-on-surface tracking-tight-display">Interview Board</h1>
              <p className="mt-2 max-w-2xl text-sm text-on-surface-variant">
                Manage and track candidate progress through the assessment funnel.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <SearchField value={query} onChange={setQuery} placeholder="Search interviews..." />
              <Button
                variant="secondary"
                className="h-11 bg-[var(--bg-layer2)] px-4 text-on-surface-variant"
                onClick={() => setActiveFilter(activeFilter === 'all' ? 'inProgress' : 'all')}
              >
                <Filter size={16} />
                {activeFilter === 'all' ? 'Filter' : stageMeta[activeFilter].title}
              </Button>
              <Button className="h-11 px-5 bg-secondary text-on-secondary hover:brightness-110" onClick={() => setScheduleOpen(true)}>
                <Plus size={17} />
                Schedule Interview
              </Button>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard icon={<Calendar size={20} />} label="Scheduled" value={interviews.filter(item => item.stage === 'scheduled').length} />
            <MetricCard icon={<Clock3 size={20} />} label="In Progress" value={interviews.filter(item => item.stage === 'inProgress').length} />
            <MetricCard icon={<CheckCircle2 size={20} />} label="Completed" value={interviews.filter(item => item.stage === 'completed').length} />
            <MetricCard icon={<Users size={20} />} label="Final Review" value={finalReviewCandidates.length} />
          </section>

          <section className="grid grid-cols-1 gap-5 xl:grid-cols-3">
            {(['scheduled', 'inProgress', 'completed'] as InterviewStage[]).map(stage => {
              const stageItems = filteredInterviews.filter(interview => interview.stage === stage);

              return (
                <div
                  key={stage}
                  className="min-h-[34rem] rounded-md bg-[var(--bg-layer1)] p-4 ghost-shadow ring-1 ring-[var(--border-ghost)]"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-semibold uppercase tracking-architectural text-on-surface">
                        {stageMeta[stage].title}
                      </h2>
                      <span className="rounded-full bg-surface-variant/50 px-2 py-0.5 text-xs font-semibold text-on-surface-variant">
                        {stageItems.length}
                      </span>
                    </div>
                    <MoreHorizontal size={20} className="text-on-surface-variant" />
                  </div>

                  <div className="space-y-4">
                    {stageItems.map(interview => (
                      <InterviewCard
                        key={interview.id}
                        interview={interview}
                        onOpen={() => setSelectedInterviewId(interview.id)}
                      />
                    ))}

                    {stageItems.length === 0 && (
                      <button
                        onClick={() => setScheduleOpen(true)}
                        className="flex h-28 w-full items-center justify-center rounded-md border border-dashed border-outline-variant/60 text-sm text-tertiary transition-colors hover:border-secondary/70 hover:text-secondary"
                      >
                        <Plus size={22} />
                        <span className="ml-2">{stageMeta[stage].empty}</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </section>
        </div>
      )}

      <ScheduleInterviewModal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        candidates={scheduleCandidates}
        candidateSearch={candidateSearch}
        selectedCandidateId={selectedCandidateId}
        selectedInterviewer={selectedInterviewer}
        scheduledDate={scheduledDate}
        scheduledTime={scheduledTime}
        meetingLink={meetingLink}
        isScheduling={assignInterview.isPending}
        onCandidateSearch={setCandidateSearch}
        onCandidate={setSelectedCandidateId}
        onInterviewer={setSelectedInterviewer}
        onScheduledDate={setScheduledDate}
        onScheduledTime={setScheduledTime}
        onMeetingLink={setMeetingLink}
        onSchedule={handleScheduleInterview}
      />
    </AppShell>
  );
}

function SearchField({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="relative block min-w-0 sm:w-80">
      <Search size={17} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-tertiary" />
      <input
        value={value}
        onChange={event => onChange(event.target.value)}
        placeholder={placeholder}
        className="h-11 w-full rounded-md bg-[var(--bg-layer2)] py-2 pl-11 pr-4 text-sm text-on-surface outline-none ring-1 ring-[var(--border-ghost)] transition focus:ring-2 focus:ring-secondary/40"
      />
    </label>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <Card className="bg-[var(--bg-layer1)] ring-1 ring-[var(--border-ghost)]">
      <div className="flex items-start justify-between">
        <div
          className="flex h-11 w-11 items-center justify-center rounded-md bg-secondary-container/25 text-secondary"
        >
          {icon}
        </div>
        <span className="text-xs font-semibold text-secondary">Total</span>
      </div>
      <p className="mt-6 text-2xl font-bold text-on-surface">{value}</p>
      <p className="text-xs font-semibold uppercase tracking-architectural text-on-surface-variant">{label}</p>
    </Card>
  );
}

function InterviewCard({ interview, onOpen }: { interview: InterviewItem; onOpen: () => void }) {
  const completed = interview.stage === 'completed';

  return (
    <button
      onClick={onOpen}
      className={cn(
        'w-full rounded-md bg-[var(--bg-layer2)] p-5 text-left transition-all hover:-translate-y-0.5 hover:ring-2 hover:ring-secondary/40',
        'ring-1 ring-[var(--border-ghost)]',
        interview.stage === 'inProgress' && 'ring-2 ring-secondary/40',
        completed && 'opacity-80',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <Badge
          variant="success"
          className="uppercase tracking-architectural"
        >
          {interview.round.replace(' Interview', '')}
        </Badge>
        {interview.stage === 'inProgress' ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-tertiary">
            <span className="h-2 w-2 rounded-full bg-secondary-container" />
            Live
          </span>
        ) : completed ? (
          <CheckCircle2 size={16} className="text-secondary" />
        ) : null}
      </div>

      <h3 className="mt-5 text-xl font-semibold text-on-surface">{interview.candidate.name}</h3>
      <p className="mt-1 text-sm text-on-surface-variant">{interview.role}</p>

      <div className="mt-7 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 text-xs text-tertiary">
          <Clock3 size={15} />
          {interview.stage === 'scheduled'
            ? `${interview.dateLabel}, ${interview.timeLabel}`
            : interview.stage === 'inProgress'
              ? 'Round 3 of 4'
              : interview.candidate.status === 'selected'
                ? 'Hire'
                : 'Awaiting decision'}
        </span>
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary/20 text-xs font-bold text-secondary ring-1 ring-secondary/30">
          {initials(interview.interviewer)}
        </span>
      </div>
    </button>
  );
}

function ScheduleInterviewModal({
  open,
  onClose,
  candidates,
  candidateSearch,
  selectedCandidateId,
  selectedInterviewer,
  scheduledDate,
  scheduledTime,
  meetingLink,
  isScheduling,
  onCandidateSearch,
  onCandidate,
  onInterviewer,
  onScheduledDate,
  onScheduledTime,
  onMeetingLink,
  onSchedule,
}: {
  open: boolean;
  onClose: () => void;
  candidates: Candidate[];
  candidateSearch: string;
  selectedCandidateId: string;
  selectedInterviewer: string;
  scheduledDate: string;
  scheduledTime: string;
  meetingLink: string;
  isScheduling: boolean;
  onCandidateSearch: (value: string) => void;
  onCandidate: (value: string) => void;
  onInterviewer: (value: string) => void;
  onScheduledDate: (value: string) => void;
  onScheduledTime: (value: string) => void;
  onMeetingLink: (value: string) => void;
  onSchedule: () => void;
}) {
  return (
    <Modal open={open} onClose={onClose} className="max-w-xl overflow-hidden bg-surface p-0">
      <div className="border-b border-outline-variant/30 bg-surface px-6 pb-5 pt-6">
        <h2 className="text-2xl font-bold text-on-surface tracking-tight-display">Schedule New Interview</h2>
        <p className="mt-1 text-sm text-on-surface-variant">Configure meeting details and assignments.</p>
      </div>

      <div className="space-y-6 bg-surface-container-lowest px-6 py-6">
        <Field label="Candidate">
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-tertiary" />
            <input
              value={candidateSearch}
              onChange={event => onCandidateSearch(event.target.value)}
              placeholder="Search candidate name..."
              className="h-12 w-full rounded-md bg-surface-container-lowest pl-12 pr-4 text-sm text-on-surface outline-none ring-1 ring-outline-variant/50 focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          {candidateSearch && (
            <div className="mt-2 max-h-28 overflow-y-auto rounded-md bg-surface-container-low p-2">
              {candidates.slice(0, 4).map(candidate => (
                <button
                  key={candidate.id}
                  type="button"
                  onClick={() => {
                    onCandidate(candidate.id);
                    onCandidateSearch(candidate.name);
                  }}
                  className={cn(
                    'w-full rounded px-2 py-1.5 text-left text-sm text-on-surface transition hover:bg-secondary-container/25',
                    selectedCandidateId === candidate.id && 'bg-secondary-container/30 text-secondary',
                  )}
                >
                  {candidate.name}
                </button>
              ))}
              {candidates.length === 0 && <p className="px-2 py-1.5 text-sm text-tertiary">No candidates found</p>}
            </div>
          )}
        </Field>

        <Field label="Assign Interviewer">
          <div className="flex flex-wrap gap-3">
            {interviewers.map(interviewer => {
              const active = selectedInterviewer === interviewer.id;
              return (
                <button
                  key={interviewer.id}
                  onClick={() => onInterviewer(interviewer.id)}
                  className={cn(
                    'w-24 rounded-md p-3 text-center transition ring-1',
                    active
                      ? 'bg-secondary-container/30 text-secondary ring-secondary'
                      : 'bg-surface-container-lowest text-on-surface-variant ring-outline-variant/50 hover:ring-secondary/50',
                  )}
                >
                  <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-secondary/20 text-sm font-bold text-secondary">
                    {initials(interviewer.name)}
                  </span>
                  <span className="mt-2 block truncate text-xs font-semibold">{interviewer.name}</span>
                </button>
              );
            })}
            <button className="w-24 rounded-md border border-dashed border-outline-variant/70 p-3 text-center text-tertiary transition hover:border-secondary hover:text-secondary">
              <UserPlus size={22} className="mx-auto mt-2" />
              <span className="mt-3 block text-xs">Add</span>
            </button>
          </div>
        </Field>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Date">
            <IconInput
              icon={<Calendar size={17} />}
              type="date"
              value={scheduledDate}
              onChange={event => onScheduledDate(event.target.value)}
            />
          </Field>
          <Field label="Time">
            <IconInput
              icon={<Clock3 size={17} />}
              type="time"
              value={scheduledTime}
              onChange={event => onScheduledTime(event.target.value)}
            />
          </Field>
        </div>

        <Field label="Meeting Link">
          <IconInput
            icon={<Video size={18} />}
            value={meetingLink}
            onChange={event => onMeetingLink(event.target.value)}
            placeholder="https://meet.google.com/abc-defg-hij"
          />
        </Field>
      </div>

      <div className="flex justify-end gap-4 border-t border-outline-variant/30 bg-surface px-6 py-5">
        <Button variant="ghost" onClick={onClose} className="px-5">
          Cancel
        </Button>
        <Button
          onClick={onSchedule}
          className="bg-secondary px-7 text-on-secondary"
          disabled={!selectedCandidateId}
          isLoading={isScheduling}
        >
          Schedule
        </Button>
      </div>
    </Modal>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-3 block text-sm font-medium uppercase tracking-architectural text-on-surface-variant">
        {label}
      </span>
      {children}
    </label>
  );
}

function IconInput({
  icon,
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { icon: React.ReactNode }) {
  return (
    <div className="relative">
      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-tertiary">{icon}</span>
      <input
        {...props}
        className={cn(
          'h-12 w-full rounded-md bg-surface-container-lowest pl-12 pr-4 text-sm text-on-surface outline-none ring-1 ring-outline-variant/50 focus:ring-2 focus:ring-secondary/50',
          className,
        )}
      />
    </div>
  );
}

function EvaluationView({
  interview,
  scoreCards,
  technicalScore,
  communicationScore,
  cultureScore,
  notes,
  isSubmitting,
  onBack,
  onTechnicalScore,
  onCommunicationScore,
  onCultureScore,
  onNotes,
  onSubmit,
}: {
  interview: InterviewItem;
  scoreCards: Array<{ round: number; score: number; maxScore: number }>;
  technicalScore: number;
  communicationScore: number;
  cultureScore: number;
  notes: string;
  isSubmitting: boolean;
  onBack: () => void;
  onTechnicalScore: (value: number) => void;
  onCommunicationScore: (value: number) => void;
  onCultureScore: (value: number) => void;
  onNotes: (value: string) => void;
  onSubmit: (recommendation: 'select' | 'reject') => void;
}) {
  const { candidate } = interview;

  return (
    <div className="space-y-6">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-architectural text-on-surface-variant transition hover:text-secondary"
      >
        <ArrowLeft size={17} />
        Back to Interviews
      </button>

      <div className="grid gap-6 xl:grid-cols-[minmax(20rem,0.95fr)_minmax(26rem,1.25fr)]">
        <div className="space-y-5">
          <Card className="bg-[var(--bg-layer1)] ring-1 ring-[var(--border-ghost)]">
            <div className="flex flex-col items-center text-center">
              <div className="relative">
                <div className="flex h-32 w-32 items-center justify-center rounded-full bg-secondary/20 text-3xl font-bold text-secondary ring-4 ring-secondary/20">
                  {initials(candidate.name)}
                </div>
                <span className="absolute bottom-3 right-1 h-5 w-5 rounded-full bg-secondary-container ring-4 ring-[var(--bg-layer1)]" />
              </div>
              <h1 className="mt-7 text-3xl font-bold text-on-surface tracking-tight-display">{candidate.name}</h1>
              <p className="mt-2 font-semibold text-secondary">{candidate.branch}</p>
              <div className="mt-7 flex gap-3">
                <IconButton icon={<ExternalLink size={18} />} label="Open profile" />
                <IconButton icon={<Video size={18} />} label="Open meeting" />
                <IconButton icon={<MessageSquareText size={18} />} label="Message" />
              </div>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-4 border-t border-outline-variant/20 pt-6">
              <ProfileFact label="College" value={candidate.college} />
              <ProfileFact label="CGPA" value={candidate.cgpa.toString()} />
              <ProfileFact label="Interview" value={interview.round} />
              <ProfileFact label="Interviewer" value={interview.interviewer} />
            </div>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            {scoreCards.map(score => (
              <Card key={score.round} className="bg-[var(--bg-layer1)] ring-1 ring-secondary/40">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold uppercase tracking-architectural text-on-surface-variant">
                    Round {score.round}
                  </p>
                  <Badge variant="success">
                    {score.score >= 80 ? 'Top 5%' : 'Strong'}
                  </Badge>
                </div>
                <p className="mt-8 text-3xl font-bold text-on-surface">
                  {score.score}
                  <span className="text-base font-medium text-on-surface-variant">/{score.maxScore}</span>
                </p>
              </Card>
            ))}
          </div>

          <Card className="bg-[var(--bg-layer1)] ring-1 ring-[var(--border-ghost)]">
            <div className="mb-5 flex items-center gap-3">
              <FileText size={22} className="text-secondary" />
              <h2 className="text-xl font-bold text-on-surface">Resume Summary</h2>
            </div>
            <p className="text-sm leading-7 text-on-surface-variant">
              Strong candidate profile with experience across {candidate.branch}, collaborative delivery, and applied
              problem solving. Review portfolio details, assessment performance, and interview evidence before making a
              final recommendation.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {[candidate.branch, candidate.college, 'Assessment Ready'].map(tag => (
                <span key={tag} className="rounded-full bg-surface-variant/40 px-3 py-1 text-xs text-on-surface">
                  {tag}
                </span>
              ))}
            </div>
          </Card>
        </div>

        <Card className="bg-surface-container-lowest p-8 text-on-surface">
          <h2 className="text-3xl font-bold tracking-tight-display">Technical Interview Evaluation</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-on-surface-variant">
            Fill in the assessment details following the session with {candidate.name}.
          </p>

          <div className="mt-10 space-y-8">
            <ScoreSlider label="Communication Skills" value={communicationScore} onChange={onCommunicationScore} />
            <ScoreSlider label="Technical Proficiency" value={technicalScore} onChange={onTechnicalScore} />
            <ScoreSlider label="Cultural Fit" value={cultureScore} onChange={onCultureScore} />
          </div>

          <label className="mt-9 block">
            <span className="mb-3 block text-sm font-medium uppercase tracking-architectural text-on-surface-variant">
              Interview Notes
            </span>
            <textarea
              value={notes}
              onChange={event => onNotes(event.target.value)}
              rows={8}
              placeholder="Document specific examples of technical depth, teamwork, or areas of concern..."
              className="w-full resize-none rounded-md bg-surface-container-low px-4 py-4 text-sm leading-6 text-on-surface outline-none ring-1 ring-outline-variant/50 focus:ring-2 focus:ring-secondary/50"
            />
          </label>

          <div className="mt-9 flex flex-col gap-4 border-t border-outline-variant/30 pt-8 sm:flex-row">
            <Button
              className="h-12 flex-1 bg-secondary text-on-secondary"
              isLoading={isSubmitting}
              onClick={() => onSubmit('select')}
            >
              <CheckCircle2 size={20} />
              Pass Candidate
            </Button>
            <Button
              variant="secondary"
              className="h-12 flex-1 border-outline-variant/70 text-on-surface-variant hover:bg-surface-container-low"
              disabled={isSubmitting}
              onClick={() => onSubmit('reject')}
            >
              <XCircle size={20} />
              Reject Candidate
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

function IconButton({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <button
      title={label}
      className="flex h-11 w-11 items-center justify-center rounded-md bg-surface-variant/30 text-on-surface-variant ring-1 ring-[var(--border-ghost)] transition hover:text-secondary hover:ring-secondary/40"
    >
      {icon}
    </button>
  );
}

function ProfileFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-architectural text-on-surface-variant">{label}</p>
      <p className="mt-2 text-sm font-semibold text-on-surface">{value}</p>
    </div>
  );
}

function ScoreSlider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="mb-4 flex items-center justify-between text-sm font-medium uppercase tracking-architectural text-on-surface-variant">
        {label}
        <strong className="text-base text-secondary">{value}/10</strong>
      </span>
      <input
        type="range"
        min="0"
        max="10"
        value={value}
        onChange={event => onChange(Number(event.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-on-surface-variant/30 accent-secondary"
      />
    </label>
  );
}
