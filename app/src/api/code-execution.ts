/**
 * Code execution API client for Piston integration
 */

import { api } from './client';

export interface CodeExecutionRequest {
  language: string;
  code: string;
  stdin?: string;
}

export interface CodeExecutionResponse {
  status: 'SUCCESS' | 'COMPILE_ERROR' | 'RUNTIME_ERROR' | 'TIMEOUT';
  stdout: string;
  stderr: string;
  exit_code: number | null;
  execution_time_ms?: number | null;
}

export interface TestCase {
  input: string;
  expected_output: string;
}

export interface EvaluationRequest {
  language: string;
  code: string;
  test_cases: TestCase[];
}

export interface TestResult {
  test_number: number;
  status: 'PASSED' | 'FAILED';
  reason?: string;
  input: string;
  expected: string;
  actual: string;
  error?: string;
}

export interface EvaluationResponse {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  score_percentage: number;
  test_results: TestResult[];
}

/**
 * Execute code with custom input (for "Run Code" button)
 */
export const executeCode = async (
  request: CodeExecutionRequest
): Promise<CodeExecutionResponse> => {
  const response = await api.post<CodeExecutionResponse>(
    '/code/execute',
    request
  );
  return response;
};

/**
 * Evaluate code against multiple test cases (for submission)
 */
export const evaluateCode = async (
  request: EvaluationRequest
): Promise<EvaluationResponse> => {
  const response = await api.post<EvaluationResponse>(
    '/code/evaluate',
    request
  );
  return response;
};
