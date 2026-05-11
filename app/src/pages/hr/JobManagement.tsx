import { useState } from 'react';
import { Briefcase, Plus, RefreshCw, Brain } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Badge, Button, Modal, Input, Select } from '../../components/ui';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { jobsApi, type Job } from '../../api/jobs';
import { useGenerateQuestion } from '../../hooks/useWorkflow';

export default function JobManagement() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showQuestionGen, setShowQuestionGen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  
  // Question generation form
  const [questionTopic, setQuestionTopic] = useState('');
  const [questionDifficulty, setQuestionDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: jobsApi.getAll,
  });

  const createJob = useMutation({
    mutationFn: (data: { 
      title: string; 
      job_description: string;
      skillset: string[];
    }) => jobsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
    },
  });

  const updateJob = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { status?: string } }) => jobsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  const generateQuestion = useGenerateQuestion();

  const handleGenerateQuestion = async () => {
    if (!questionTopic.trim()) {
      alert('Please enter a topic for the question');
      return;
    }

    try {
      const result = await generateQuestion.mutateAsync({
        topic: questionTopic,
        difficulty: questionDifficulty,
        num_public_cases: 2,
        num_private_cases: 3,
      });
      
      alert(`Question "${result.title}" generated successfully!`);
      setShowQuestionGen(false);
      setQuestionTopic('');
      setSelectedJob(null);
    } catch (error) {
      alert(`Failed to generate question: ${error}`);
    }
  };

  const columns: Column<Job>[] = [
    {
      key: 'title',
      header: 'Job Title',
      render: (j) => (
        <div className="flex items-center gap-2">
          <Briefcase size={14} className="text-secondary" />
          <span className="font-medium text-on-surface">{j.title}</span>
        </div>
      ),
    },
    {
      key: 'location',
      header: 'Location',
      render: (j) => <span className="text-sm text-tertiary">{j.location}</span>,
    },
    {
      key: 'openings',
      header: 'Openings',
      render: (j) => <span className="font-mono text-xs">{j.openings}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (j) => (
        <Badge variant={j.status === 'OPEN' ? 'success' : 'default'}>
          {j.status}
        </Badge>
      ),
    },
    {
      key: 'actions' as keyof Job,
      header: 'Actions',
      render: (j) => (
        <div className="flex gap-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={(e) => { 
              e.stopPropagation(); 
              setSelectedJob(j);
              setShowQuestionGen(true);
            }}
          >
            <Brain size={12} />
            Generate Questions
          </Button>
          {(j.status === 'OPEN') ? (
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => { e.stopPropagation(); updateJob.mutate({ id: j.id, data: { status: 'CLOSED' } }); }}
            >
              Close
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={(e) => { e.stopPropagation(); updateJob.mutate({ id: j.id, data: { status: 'OPEN' } }); }}
            >
              Reopen
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppShell title="Job Management">
      <div className="space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Briefcase size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-widest">Total Jobs</p>
                <p className="text-xl font-bold text-on-surface">{jobs?.length ?? 0}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <RefreshCw size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-widest">Active</p>
                <p className="text-xl font-bold text-on-surface">
                  {jobs?.filter(j => j.status === 'OPEN').length ?? 0}
                </p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary/10">
                <Briefcase size={18} className="text-secondary" />
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase tracking-widest">Closed</p>
                <p className="text-xl font-bold text-on-surface">
                  {jobs?.filter(j => j.status === 'CLOSED' || j.status === 'DRAFT').length ?? 0}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Create Job Panel */}
        {showCreate && (
          <Card>
            <CardTitle>Create New Job</CardTitle>
            <div className="mt-3 space-y-3">
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="Job title (e.g. Software Engineer Intern)"
                className="w-full px-3 py-2 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface
                           focus:outline-none focus:ring-2 focus:ring-secondary/50 placeholder:text-tertiary"
              />
              <textarea
                value={newDesc}
                onChange={e => setNewDesc(e.target.value)}
                placeholder="Job description..."
                rows={3}
                className="w-full px-3 py-2 rounded-md bg-[var(--bg-layer1)] text-sm text-on-surface
                           focus:outline-none focus:ring-2 focus:ring-secondary/50 placeholder:text-tertiary resize-none"
              />
              <div className="flex gap-2 justify-end">
                <Button variant="secondary" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  size="sm"
                  isLoading={createJob.isPending}
                  onClick={() => {
                    if (newName.trim() && newDesc.trim()) {
                      createJob.mutate({ 
                        title: newName.trim(), 
                        job_description: newDesc.trim(),
                        skillset: ['Programming', 'Problem Solving'] // Default skills
                      });
                    }
                  }}
                >
                  Create Job
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Job Table */}
        <Card padding="none">
          <div className="p-4 bg-[var(--bg-layer1)] flex items-center justify-between">
            <CardTitle>Jobs / Hiring Cycles</CardTitle>
            <Button size="sm" onClick={() => setShowCreate(true)}>
              <Plus size={14} />
              New Job
            </Button>
          </div>
          {isLoading ? (
            <div className="p-8 text-center text-sm text-tertiary">Loading jobs...</div>
          ) : (
            <DataTable
              columns={columns}
              data={jobs ?? []}
              keyExtractor={j => j.id}
            />
          )}
        </Card>

        {/* Question Generation Modal */}
        <Modal
          open={showQuestionGen}
          onClose={() => setShowQuestionGen(false)}
          title={`Generate Questions for ${selectedJob?.title || 'Job'}`}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">
                Question Topic
              </label>
              <Input
                value={questionTopic}
                onChange={(e) => setQuestionTopic(e.target.value)}
                placeholder="e.g., arrays and loops, data structures, algorithms"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">
                Difficulty Level
              </label>
              <Select
                value={questionDifficulty}
                onChange={(e) => setQuestionDifficulty(e.target.value as 'easy' | 'medium' | 'hard')}
                options={[
                  { value: 'easy', label: 'Easy' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'hard', label: 'Hard' },
                ]}
              />
            </div>

            <div className="flex gap-2 justify-end pt-4">
              <Button 
                variant="secondary" 
                onClick={() => setShowQuestionGen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleGenerateQuestion}
                disabled={generateQuestion.isPending || !questionTopic.trim()}
              >
                <Brain size={14} />
                {generateQuestion.isPending ? 'Generating...' : 'Generate Question'}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </AppShell>
  );
}
