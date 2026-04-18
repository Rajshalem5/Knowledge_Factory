import { useState } from 'react';
import { Button, Badge } from '../../components/ui';
import { Timer } from '../../components/assessment/Timer';
import { ProblemPanel } from '../../components/assessment/ProblemPanel';
import { CodeEditor } from '../../components/assessment/CodeEditor';
import { TestOutput } from '../../components/assessment/TestOutput';
import { useSubmitSection } from '../../hooks/useAssessment';
import { Play, Send } from 'lucide-react';

const SAMPLE_PROBLEM = {
  id: 'p1',
  title: 'Two Sum',
  description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

**Example 1:**
Input: nums = [2,7,11,15], target = 9
Output: [0,1]

**Constraints:**
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- Only one valid answer exists`,
  difficulty: 'easy' as const,
  starterCode: `function twoSum(nums, target) {\n  // Write your solution here\n  \n}`,
  testCases: [
    { id: 't1', input: 'nums = [2,7,11,15], target = 9', expectedOutput: '[0,1]', isHidden: false },
    { id: 't2', input: 'nums = [3,2,4], target = 6', expectedOutput: '[1,2]', isHidden: false },
    { id: 't3', input: 'nums = [3,3], target = 6', expectedOutput: '[0,1]', isHidden: true },
  ],
};

export default function Assessment() {
  const [code, setCode] = useState(SAMPLE_PROBLEM.starterCode);
  const [testResults, setTestResults] = useState<Array<{ name: string; passed: boolean; input: string; expected: string; actual?: string }>>([]);
  const submitSection = useSubmitSection();

  const handleRun = () => {
    setTestResults([
      { name: 'Test 1', passed: true, input: '[2,7,11,15], 9', expected: '[0,1]', actual: '[0,1]' },
      { name: 'Test 2', passed: true, input: '[3,2,4], 6', expected: '[1,2]', actual: '[1,2]' },
    ]);
  };

  const handleSubmit = () => {
    submitSection.mutate(
      { assessmentId: 'current', data: { problemId: SAMPLE_PROBLEM.id, code } },
      {
        onSuccess: (result) => {
          setTestResults([
            { name: 'Visible Tests', passed: true, input: '', expected: '', actual: '' },
            { name: 'Hidden Tests', passed: result.passed > result.failed, input: '', expected: '' },
          ]);
        },
      },
    );
  };

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-base)]">
      {/* Assessment Header */}
      <div className="flex items-center justify-between px-4 h-12 bg-[var(--bg-layer1)]">
        <div className="flex items-center gap-3">
          <Badge variant="warning">Round 1</Badge>
          <span className="text-sm font-medium text-on-surface">Assessment</span>
        </div>
        <Timer initialSeconds={3600} className="!text-base" />
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleRun}>
            <Play size={12} />
            Run
          </Button>
          <Button size="sm" onClick={handleSubmit} isLoading={submitSection.isPending}>
            <Send size={12} />
            Submit
          </Button>
        </div>
      </div>

      {/* Split Panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Problem */}
        <div className="w-1/2 overflow-y-auto bg-[var(--bg-base)]">
          <ProblemPanel problem={SAMPLE_PROBLEM} />
        </div>

        {/* Right: Editor + Output */}
        <div className="w-1/2 flex flex-col bg-[var(--bg-layer1)]">
          {/* Editor */}
          <div className="flex-1 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 bg-[var(--bg-layer1)]">
              <span className="text-xs text-tertiary uppercase tracking-architectural">Solution</span>
              <Badge variant="default">JavaScript</Badge>
            </div>
            <CodeEditor initialValue={SAMPLE_PROBLEM.starterCode} onChange={setCode} className="h-full" />
          </div>

          {/* Output */}
          <div className="h-48 bg-[var(--bg-base)]">
            <TestOutput results={testResults} className="h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
