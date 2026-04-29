/**
 * Hook for code execution and evaluation
 */

import { useState } from 'react';
import {
  executeCode,
  evaluateCode,
  type CodeExecutionRequest,
  type CodeExecutionResponse,
  type EvaluationRequest,
  type EvaluationResponse,
} from '../api/code-execution';

export const useCodeExecution = () => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [executionResult, setExecutionResult] = useState<CodeExecutionResponse | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Execute code with custom input (Run Code button)
   */
  const runCode = async (request: CodeExecutionRequest) => {
    setIsExecuting(true);
    setError(null);
    setExecutionResult(null);

    try {
      const result = await executeCode(request);
      setExecutionResult(result);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to execute code';
      setError(errorMessage);
      throw err;
    } finally {
      setIsExecuting(false);
    }
  };

  /**
   * Evaluate code against test cases (Submit button)
   */
  const evaluate = async (request: EvaluationRequest) => {
    setIsEvaluating(true);
    setError(null);
    setEvaluationResult(null);

    try {
      const result = await evaluateCode(request);
      setEvaluationResult(result);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to evaluate code';
      setError(errorMessage);
      throw err;
    } finally {
      setIsEvaluating(false);
    }
  };

  /**
   * Clear results and errors
   */
  const clearResults = () => {
    setExecutionResult(null);
    setEvaluationResult(null);
    setError(null);
  };

  return {
    // State
    isExecuting,
    isEvaluating,
    executionResult,
    evaluationResult,
    error,

    // Actions
    runCode,
    evaluate,
    clearResults,
  };
};
