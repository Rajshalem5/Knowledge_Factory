# Monaco Editor Integration Guide

Complete guide for integrating the backend with Monaco Editor frontend.

## Frontend Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── CodeEditor.jsx       # Monaco editor wrapper
│   │   ├── TestCasePanel.jsx    # Test case display
│   │   └── MCQPanel.jsx         # MCQ questions
│   ├── services/
│   │   └── api.js               # API client
│   └── pages/
│       └── Assessment.jsx       # Main assessment page
```

## 1. API Client Setup

```javascript
// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const assessmentAPI = {
  // Start assessment
  startAssessment: async (candidateId) => {
    const response = await axios.post(
      `${API_BASE_URL}/api/assessment/start?candidate_id=${candidateId}`
    );
    return response.data;
  },

  // Get questions
  getQuestions: async (assessmentId) => {
    const response = await axios.get(
      `${API_BASE_URL}/api/assessment/${assessmentId}/questions`
    );
    return response.data;
  },

  // Execute code (Run button)
  executeCode: async (code, language, stdin) => {
    const response = await axios.post(
      `${API_BASE_URL}/api/code/execute`,
      { code, language, stdin }
    );
    return response.data;
  },

  // Submit assessment
  submitAssessment: async (assessmentId, submission) => {
    const response = await axios.post(
      `${API_BASE_URL}/api/assessment/submit?assessment_id=${assessmentId}`,
      submission
    );
    return response.data;
  },

  // Get result
  getResult: async (candidateId) => {
    const response = await axios.get(
      `${API_BASE_URL}/api/assessment/result?candidate_id=${candidateId}`
    );
    return response.data;
  }
};
```

## 2. Monaco Editor Component

```jsx
// src/components/CodeEditor.jsx
import React, { useRef, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

const CodeEditor = ({ 
  problem, 
  onCodeChange, 
  onRun 
}) => {
  const editorRef = useRef(null);
  const [code, setCode] = useState(problem.boilerplate);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Configure editor
    monaco.editor.defineTheme('customTheme', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#1e1e1e',
      }
    });
    monaco.editor.setTheme('customTheme');
  };

  const handleCodeChange = (value) => {
    setCode(value);
    onCodeChange(value);
  };

  const handleRun = async () => {
    setIsRunning(true);
    setOutput('Running...');
    
    try {
      // Use first visible test case as default input
      const testCase = problem.visible_test_cases[0];
      const result = await assessmentAPI.executeCode(
        code,
        'python',
        testCase.input
      );
      
      if (result.stderr) {
        setOutput(`Error:\n${result.stderr}`);
      } else {
        setOutput(`Output:\n${result.stdout}\n\nExpected:\n${testCase.output}\n\nTime: ${result.time}ms\nMemory: ${result.memory}KB`);
      }
    } catch (error) {
      setOutput(`Execution failed: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="code-editor-container">
      <div className="editor-header">
        <h3>{problem.title}</h3>
        <button 
          onClick={handleRun} 
          disabled={isRunning}
          className="run-button"
        >
          {isRunning ? 'Running...' : 'Run Code'}
        </button>
      </div>
      
      <div className="problem-description">
        <p>{problem.description}</p>
        
        <h4>Test Cases:</h4>
        {problem.visible_test_cases.map((tc, idx) => (
          <div key={idx} className="test-case">
            <strong>Input:</strong>
            <pre>{tc.input}</pre>
            <strong>Output:</strong>
            <pre>{tc.output}</pre>
          </div>
        ))}
      </div>

      <Editor
        height="400px"
        defaultLanguage="python"
        value={code}
        onChange={handleCodeChange}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />

      <div className="output-panel">
        <h4>Output:</h4>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default CodeEditor;
```

## 3. Main Assessment Page

```jsx
// src/pages/Assessment.jsx
import React, { useState, useEffect } from 'react';
import CodeEditor from '../components/CodeEditor';
import MCQPanel from '../components/MCQPanel';
import { assessmentAPI } from '../services/api';

const Assessment = ({ candidateId }) => {
  const [assessmentId, setAssessmentId] = useState(null);
  const [questions, setQuestions] = useState(null);
  const [currentProblem, setCurrentProblem] = useState(0);
  const [codingSolutions, setCodingSolutions] = useState({});
  const [mcqAnswers, setMcqAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(40 * 60); // 40 minutes

  useEffect(() => {
    initializeAssessment();
  }, []);

  useEffect(() => {
    // Timer countdown
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const initializeAssessment = async () => {
    try {
      // Start assessment
      const assessment = await assessmentAPI.startAssessment(candidateId);
      setAssessmentId(assessment.assessment_id);

      // Load questions
      const qs = await assessmentAPI.getQuestions(assessment.assessment_id);
      setQuestions(qs);

      // Initialize solutions
      const initialSolutions = {};
      qs.coding.forEach(problem => {
        initialSolutions[problem.id] = problem.boilerplate;
      });
      setCodingSolutions(initialSolutions);
    } catch (error) {
      console.error('Failed to initialize assessment:', error);
    }
  };

  const handleCodeChange = (problemId, code) => {
    setCodingSolutions(prev => ({
      ...prev,
      [problemId]: code
    }));
  };

  const handleMCQAnswer = (questionId, answer) => {
    setMcqAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmit = async () => {
    if (!window.confirm('Are you sure you want to submit?')) {
      return;
    }

    try {
      // Prepare submission
      const submission = {
        coding: questions.coding.map(problem => ({
          question_id: problem.id,
          code: codingSolutions[problem.id],
          language: 'python'
        })),
        mcq_answers: mcqAnswers
      };

      // Submit
      await assessmentAPI.submitAssessment(assessmentId, submission);

      // Redirect to results
      window.location.href = `/result?candidate_id=${candidateId}`;
    } catch (error) {
      alert('Submission failed: ' + error.message);
    }
  };

  if (!questions) {
    return <div>Loading assessment...</div>;
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="assessment-container">
      <header className="assessment-header">
        <h1>Round 2 Assessment</h1>
        <div className="timer">
          Time Remaining: {formatTime(timeRemaining)}
        </div>
        <button onClick={handleSubmit} className="submit-button">
          Submit Assessment
        </button>
      </header>

      <div className="assessment-content">
        {/* Coding Problems */}
        <section className="coding-section">
          <h2>Coding Problems</h2>
          <div className="problem-tabs">
            {questions.coding.map((problem, idx) => (
              <button
                key={problem.id}
                onClick={() => setCurrentProblem(idx)}
                className={currentProblem === idx ? 'active' : ''}
              >
                Problem {idx + 1}
              </button>
            ))}
          </div>

          <CodeEditor
            problem={questions.coding[currentProblem]}
            onCodeChange={(code) => 
              handleCodeChange(questions.coding[currentProblem].id, code)
            }
          />
        </section>

        {/* MCQ Section */}
        <section className="mcq-section">
          <h2>Multiple Choice Questions</h2>
          <MCQPanel
            questions={questions.mcq}
            answers={mcqAnswers}
            onAnswer={handleMCQAnswer}
          />
        </section>
      </div>
    </div>
  );
};

export default Assessment;
```

## 4. MCQ Component

```jsx
// src/components/MCQPanel.jsx
import React from 'react';

const MCQPanel = ({ questions, answers, onAnswer }) => {
  return (
    <div className="mcq-panel">
      {questions.map((question, idx) => (
        <div key={question.id} className="mcq-question">
          <h4>Question {idx + 1}</h4>
          <p>{question.question}</p>
          
          <div className="mcq-options">
            {question.options.map(option => (
              <label key={option.id} className="mcq-option">
                <input
                  type="radio"
                  name={question.id}
                  value={option.id}
                  checked={answers[question.id] === option.id}
                  onChange={() => onAnswer(question.id, option.id)}
                />
                <span>{option.id}. {option.text}</span>
              </label>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MCQPanel;
```

## 5. Result Page

```jsx
// src/pages/Result.jsx
import React, { useEffect, useState } from 'react';
import { assessmentAPI } from '../services/api';

const Result = ({ candidateId }) => {
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadResult();
  }, []);

  const loadResult = async () => {
    try {
      const data = await assessmentAPI.getResult(candidateId);
      setResult(data);
    } catch (error) {
      console.error('Failed to load result:', error);
    }
  };

  if (!result) {
    return <div>Loading results...</div>;
  }

  return (
    <div className="result-container">
      <h1>Assessment Result</h1>
      
      <div className={`verdict ${result.verdict.toLowerCase()}`}>
        {result.verdict}
      </div>

      <div className="score-breakdown">
        <div className="score-item">
          <h3>Total Score</h3>
          <p className="score">{result.total_score.toFixed(1)}</p>
        </div>

        <div className="score-item">
          <h3>Coding Score</h3>
          <p className="score">{result.coding_score.toFixed(1)}%</p>
        </div>

        <div className="score-item">
          <h3>MCQ Score</h3>
          <p className="score">{result.mcq_score}/10</p>
        </div>
      </div>

      {result.evaluation_details && (
        <div className="details">
          <h3>Detailed Results</h3>
          {result.evaluation_details.coding_results.map((cr, idx) => (
            <div key={idx} className="coding-result">
              <h4>Problem {idx + 1}</h4>
              <p>Passed: {cr.passed}/{cr.total} test cases</p>
              <p>Score: {cr.percentage.toFixed(1)}%</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Result;
```

## 6. Styling (CSS)

```css
/* src/styles/assessment.css */
.assessment-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.assessment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.timer {
  font-size: 24px;
  font-weight: bold;
  color: #e74c3c;
}

.code-editor-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.run-button {
  background: #27ae60;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.run-button:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.output-panel {
  margin-top: 20px;
  padding: 15px;
  background: #2c3e50;
  color: #ecf0f1;
  border-radius: 4px;
}

.mcq-panel {
  display: grid;
  gap: 20px;
}

.mcq-question {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.mcq-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 15px;
}

.mcq-option {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.mcq-option:hover {
  background: #f8f9fa;
}

.verdict {
  font-size: 48px;
  font-weight: bold;
  text-align: center;
  padding: 40px;
  border-radius: 8px;
  margin: 20px 0;
}

.verdict.pass {
  background: #d4edda;
  color: #155724;
}

.verdict.fail {
  background: #f8d7da;
  color: #721c24;
}
```

## 7. Package Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@monaco-editor/react": "^4.6.0",
    "axios": "^1.6.0"
  }
}
```

## 8. Installation

```bash
npm install @monaco-editor/react axios
```

## Key Features Implemented

✅ Monaco Editor integration with syntax highlighting
✅ Real-time code execution (Run button)
✅ Test case display (visible only)
✅ MCQ interface
✅ Timer countdown
✅ Auto-submit on timeout
✅ Result display with breakdown
✅ Responsive design

## Testing the Integration

1. Start backend: `python run.py`
2. Start frontend: `npm start`
3. Navigate to assessment page
4. Test code execution
5. Submit and view results
