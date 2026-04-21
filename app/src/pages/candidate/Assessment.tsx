import { useState } from 'react';
import { 
  Button, 
  Badge,
  Card,
  CardHeader,
  CardTitle
} from '../../components/ui';
import { 
  Timer, 
  Play, 
  Send, 
  RotateCcw, 
  FileText,
  Clock,
  Award,
  Trophy,
  Target,
  Zap
} from 'lucide-react';
import { cn } from '../../utils/cn';

// Mock problem data
const SAMPLE_PROBLEM = {
  id: 'p1',
  title: 'Two Sum',
  description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.`,
  difficulty: 'easy' as const,
  starterCode: `function twoSum(nums, target) {\n  // Write your solution here\n  \n}`,
  constraints: [
    '2 <= nums.length <= 10^4',
    '-10^9 <= nums[i] <= 10^9',
    'Only one valid answer exists'
  ],
  examples: [
    {
      input: 'nums = [2,7,11,15], target = 9',
      output: '[0,1]',
      explanation: 'Because nums[0] + nums[1] == 9, we return [0, 1].'
    }
  ],
  testCases: [
    { id: 't1', input: 'nums = [2,7,11,15], target = 9', expected: '[0,1]', hidden: false },
    { id: 't2', input: 'nums = [3,2,4], target = 6', expected: '[1,2]', hidden: false },
    { id: 't3', input: 'nums = [3,3], target = 6', expected: '[0,1]', hidden: true },
  ],
};

// Mock test results
const MOCK_TEST_RESULTS = [
  { name: 'Test Case 1', passed: true, input: '[2,7,11,15], 9', expected: '[0,1]', actual: '[0,1]' },
  { name: 'Test Case 2', passed: true, input: '[3,2,4], 6', expected: '[1,2]', actual: '[1,2]' },
  { name: 'Test Case 3', passed: false, input: '[3,3], 6', expected: '[0,1]', actual: '[1,1]' },
];

export default function Assessment() {
  const [code, setCode] = useState(SAMPLE_PROBLEM.starterCode);
  const [testResults, setTestResults] = useState(MOCK_TEST_RESULTS);
  const [timeRemaining, setTimeRemaining] = useState(3600); // 60 minutes in seconds
  const [activeTab, setActiveTab] = useState<'problem' | 'editor' | 'output'>('problem');

  const handleRun = () => {
    setTestResults(MOCK_TEST_RESULTS);
  };

  const handleSubmit = () => {
    setTestResults([
      { name: 'Visible Tests', passed: true, input: '', expected: '', actual: '' },
      { name: 'Hidden Tests', passed: true, input: '', expected: '' },
    ]);
  };

  const handleReset = () => {
    setCode(SAMPLE_PROBLEM.starterCode);
    setTestResults([]);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-surface to-surface-container-low">
      {/* Assessment Header */}
      <div className="flex items-center justify-between px-6 h-16 bg-surface-container-lowest/80 backdrop-blur-sm border-b border-outline-variant/20 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="p-2 rounded-lg bg-gradient-to-br from-secondary to-primary">
            <FileText size={20} className="text-white" />
          </div>
          <div>
            <Badge variant="primary" className="mb-1">Round 1</Badge>
            <span className="text-lg font-semibold text-on-surface tracking-tight-display block">Technical Assessment</span>
            <span className="text-xs text-on-surface-variant">20 minutes • 2 problems</span>
          </div>
        </div>
        
        <div className="flex items-center gap-1 bg-primary/5 px-4 py-2 rounded-lg">
          <Clock size={16} className="text-primary" />
          <span className="font-mono text-primary font-medium">{formatTime(timeRemaining)}</span>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={handleReset}
            className="flex items-center gap-2 px-4"
          >
            <RotateCcw size={14} />
            Reset
          </Button>
          <Button variant="secondary" size="sm" onClick={handleRun}>
            <Play size={14} />
            Run Tests
          </Button>
          <Button size="sm" onClick={handleSubmit} className="bg-primary hover:bg-primary/90 text-on-primary">
            <Send size={14} />
            Submit
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Problem Description */}
        <div className="w-1/2 flex flex-col border-r border-outline-variant/20 overflow-hidden">
          <div className="flex border-b border-outline-variant/20">
            <button 
              className={cn(
                "flex-1 px-4 py-3 text-center font-medium",
                activeTab === 'problem' 
                  ? 'text-primary border-b-2 border-primary' 
                  : 'text-on-surface-variant hover:text-on-surface'
              )}
              onClick={() => setActiveTab('problem')}
            >
              Problem
            </button>
            <button 
              className={cn(
                "flex-1 px-4 py-3 text-center font-medium",
                activeTab === 'editor' 
                  ? 'text-primary border-b-2 border-primary' 
                  : 'text-on-surface-variant hover:text-on-surface'
              )}
              onClick={() => setActiveTab('editor')}
            >
              Editor
            </button>
            <button 
              className={cn(
                "flex-1 px-4 py-3 text-center font-medium",
                activeTab === 'output' 
                  ? 'text-primary border-b-2 border-primary' 
                  : 'text-on-surface-variant hover:text-on-surface'
              )}
              onClick={() => setActiveTab('output')}
            >
              Output
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 bg-surface-container-lowest">
            {activeTab === 'problem' ? (
              <div>
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Target size={16} className="text-primary" />
                    <h1 className="text-2xl font-bold text-on-surface">{SAMPLE_PROBLEM.title}</h1>
                    <Badge variant={SAMPLE_PROBLEM.difficulty === 'easy' ? 'success' : SAMPLE_PROBLEM.difficulty === 'medium' ? 'warning' : 'danger'}>
                      {SAMPLE_PROBLEM.difficulty.charAt(0).toUpperCase() + SAMPLE_PROBLEM.difficulty.slice(1)}
                    </Badge>
                  </div>
                  <p className="text-on-surface-variant pt-2">{SAMPLE_PROBLEM.description}</p>
                </div>

                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap size={16} className="text-primary" />
                        Examples
                      </CardTitle>
                    </CardHeader>
                    <div className="p-4">
                      {SAMPLE_PROBLEM.examples.map((example, index) => (
                        <div key={index} className="space-y-2">
                          <p className="font-medium text-on-surface">
                            Example {index + 1}:
                          </p>
                          <div className="ml-2 text-sm text-on-surface-variant">
                            Input: {example.input} 
                          </div>
                          <div className="ml-2 text-sm text-on-surface-variant">
                            Output: {example.output}
                          </div>
                          <div className="ml-2 text-sm text-on-surface-variant">
                            Explanation: {example.explanation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Award size={16} className="text-primary" />
                        Constraints
                      </CardTitle>
                    </CardHeader>
                    <div className="p-4 space-y-2">
                      {SAMPLE_PROBLEM.constraints.map((constraint, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0"></div>
                          <p className="text-sm text-on-surface-variant">{constraint}</p>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Trophy size={16} className="text-primary" />
                        Test Cases
                      </CardTitle>
                    </CardHeader>
                    <div className="p-4 space-y-3">
                      {SAMPLE_PROBLEM.testCases.map((testCase, index) => (
                        <div key={testCase.id} className="border-l-2 border-primary pl-4 py-1">
                          <p className="text-sm font-medium text-on-surface">
                            Test Case {index + 1}: 
                            <span className="ml-2 text-xs font-normal text-on-surface-variant">
                              {testCase.hidden ? '(Hidden)' : '(Visible)'}
                            </span>
                          </p>
                          <p className="text-xs text-on-surface-variant mt-1">
                            Input: {testCase.input}
                          </p>
                          <p className="text-xs text-on-surface-variant mt-1">
                            Expected: {testCase.expected}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              </div>
            ) : activeTab === 'editor' ? (
              <div className="h-full flex flex-col">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-outline-variant/20">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-success"></div>
                    <span className="text-sm font-medium text-on-surface tracking-tight-display">Solution</span>
                  </div>
                  <Badge variant="default" className="text-xs">JavaScript</Badge>
                </div>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="flex-1 font-mono text-sm p-4 bg-surface-container-low border border-outline-variant/20 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
                  spellCheck="false"
                />
              </div>
            ) : (
              <div className="h-full flex flex-col">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-outline-variant/20">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-secondary"></div>
                    <span className="text-sm font-medium text-on-surface tracking-tight-display">Test Results</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                    <span>{testResults.filter(t => t.passed).length}/{testResults.length} passed</span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {testResults.length > 0 ? (
                    <div className="space-y-3">
                      {testResults.map((result, index) => (
                        <div 
                          key={index} 
                          className={cn(
                            "p-4 rounded-lg border",
                            result.passed 
                              ? "border-success/30 bg-success/5" 
                              : "border-danger/30 bg-danger/5"
                          )}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            {result.passed ? (
                              <span className="w-2 h-2 rounded-full bg-success"></span>
                            ) : (
                              <span className="w-2 h-2 rounded-full bg-danger"></span>
                            )}
                            <span className="font-medium text-on-surface">
                              {result.name}{result.passed ? ' ✓' : ' ✗'}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {result.input && (
                              <div>
                                <p className="text-on-surface-variant">Input:</p>
                                <p className="text-on-surface">{result.input}</p>
                              </div>
                            )}
                            {result.expected && (
                              <div>
                                <p className="text-on-surface-variant">Expected:</p>
                                <p className="text-on-surface">{result.expected}</p>
                              </div>
                            )}
                            {result.actual && (
                              <div>
                                <p className="text-on-surface-variant">Actual:</p>
                                <p className="text-on-surface">{result.actual}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-center">
                      <p className="text-sm text-on-surface-variant max-w-xs">
                        No test results yet. Run your code to see results.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Output/Tests */}  
        <div className="w-1/2 flex flex-col bg-surface-container-low">
          {/* Editor Section */}
          <div className="flex-1 overflow-hidden border-b border-outline-variant/20">
            <div className="flex items-center justify-between px-4 py-3 bg-surface-container-lowest/50 border-b border-outline-variant/10">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-success"></div>
                <span className="text-sm font-medium text-on-surface tracking-tight-display">Solution</span>
              </div>
              <Badge variant="default" className="text-xs">JavaScript</Badge>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-full font-mono text-sm p-4 bg-surface-container-low border border-outline-variant/20 resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
              spellCheck="false"
            />
          </div>

          {/* Output Section */}
          <div className="h-64 bg-surface-container-lowest border-t border-outline-variant/20 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 bg-surface-container-lowest/80 border-b border-outline-variant/10">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-secondary"></div>
                <span className="text-sm font-medium text-on-surface tracking-tight-display">Test Results</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-tertiary">
                <span>{testResults.filter(t => t.passed).length}/{testResults.length} passed</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {testResults.length > 0 ? (
                <div className="space-y-3">
                  {testResults.map((result, index) => (
                    <div 
                      key={index} 
                      className={cn(
                        "p-3 rounded-lg text-sm",
                        result.passed 
                          ? "bg-success/5 text-success border border-success/20" 
                          : "bg-danger/5 text-danger border border-danger/20"
                      )}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium">
                          {result.name}{result.passed ? ' ✓' : ' ✗'}
                        </span>
                        {result.passed ? (
                          <span className="text-xs">PASSED</span>
                        ) : (
                          <span className="text-xs">FAILED</span>
                        )}
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-2">
                        <div>
                          <p className="text-xs text-on-surface-variant">Input:</p>
                          <p className="text-xs">{result.input}</p>
                        </div>
                        <div>
                          <p className="text-xs text-on-surface-variant">Expected:</p>
                          <p className="text-xs">{result.expected}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-on-surface-variant">
                  Run your code to see test results
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
