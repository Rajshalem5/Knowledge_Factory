"""Code execution service using Piston API."""

import httpx
from app.config import settings
from app.features.code_execution.schemas import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    TestCase,
    EvaluationResult,
)


class PistonExecutionService:

    LANGUAGE_VERSIONS = {
        "python": "3.12.0",
        "java": "15.0.2",
        "cpp": "10.2.0",
        "c++": "10.2.0",
        "javascript": "18.15.0",
        "c": "10.2.0",
    }

    EXECUTION_TIMEOUT = 15.0

    @property
    def piston_url(self) -> str:
        return settings.SANDBOX_URL
    
    async def execute_code(
        self, 
        language: str, 
        code: str, 
        stdin: str = ""
    ) -> CodeExecutionResponse:
        """
        Execute code using Piston API.
        
        Args:
            language: Programming language (python, java, cpp, javascript)
            code: Source code to execute
            stdin: Standard input for the program
            
        Returns:
            CodeExecutionResponse with execution results
        """
        # Normalize language name
        language = language.lower()
        if language == "c++":
            language = "cpp"
        
        # Prepare payload for Piston
        payload = {
            "language": language,
            "version": self.LANGUAGE_VERSIONS.get(language, "*"),
            "files": [
                {
                    "content": code
                }
            ],
            "stdin": stdin
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.EXECUTION_TIMEOUT) as client:
                response = await client.post(
                    self.piston_url,
                    json=payload,
                    headers={"ngrok-skip-browser-warning": "true"},
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract execution results
                run_data = data.get("run", {})
                compile_data = data.get("compile", {})
                
                # Check for compilation errors
                if compile_data.get("stderr"):
                    return CodeExecutionResponse(
                        status="COMPILE_ERROR",
                        stdout=compile_data.get("stdout", ""),
                        stderr=compile_data.get("stderr", ""),
                        exit_code=compile_data.get("code"),
                    )
                
                # Check for runtime errors
                if run_data.get("stderr"):
                    return CodeExecutionResponse(
                        status="RUNTIME_ERROR",
                        stdout=run_data.get("stdout", ""),
                        stderr=run_data.get("stderr", ""),
                        exit_code=run_data.get("code"),
                    )
                
                # Successful execution
                return CodeExecutionResponse(
                    status="SUCCESS",
                    stdout=run_data.get("stdout", ""),
                    stderr=run_data.get("stderr", ""),
                    exit_code=run_data.get("code", 0),
                )
                
        except httpx.TimeoutException:
            return CodeExecutionResponse(
                status="TIMEOUT",
                stdout="",
                stderr="Execution timed out",
                exit_code=-1,
            )
        except httpx.HTTPError as e:
            return CodeExecutionResponse(
                status="RUNTIME_ERROR",
                stdout="",
                stderr=f"HTTP error occurred: {str(e)}",
                exit_code=-1,
            )
        except Exception as e:
            return CodeExecutionResponse(
                status="RUNTIME_ERROR",
                stdout="",
                stderr=f"Unexpected error: {str(e)}",
                exit_code=-1,
            )
    
    async def evaluate_code(
        self,
        language: str,
        code: str,
        test_cases: list[TestCase]
    ) -> EvaluationResult:
        """
        Evaluate code against multiple test cases.
        
        Args:
            language: Programming language
            code: Source code to evaluate
            test_cases: List of test cases with input and expected output
            
        Returns:
            EvaluationResult with pass/fail counts and detailed results
        """
        passed = 0
        failed = 0
        test_results = []
        
        for idx, test_case in enumerate(test_cases, 1):
            # Execute code with test case input
            result = await self.execute_code(language, code, test_case.input)
            
            # Check if execution was successful
            if result.status != "SUCCESS":
                test_results.append({
                    "test_number": idx,
                    "status": "FAILED",
                    "reason": result.status,
                    "input": test_case.input,
                    "expected": test_case.expected_output,
                    "actual": result.stderr or "Execution failed",
                    "error": result.stderr,
                })
                failed += 1
                continue
            
            # Compare output with expected
            actual_output = (result.stdout or "").strip()
            expected_output = test_case.expected_output.strip()
            
            if actual_output == expected_output:
                test_results.append({
                    "test_number": idx,
                    "status": "PASSED",
                    "input": test_case.input,
                    "expected": expected_output,
                    "actual": actual_output,
                })
                passed += 1
            else:
                test_results.append({
                    "test_number": idx,
                    "status": "FAILED",
                    "reason": "OUTPUT_MISMATCH",
                    "input": test_case.input,
                    "expected": expected_output,
                    "actual": actual_output,
                })
                failed += 1
        
        total = len(test_cases)
        score_percentage = (passed / total * 100) if total > 0 else 0
        
        return EvaluationResult(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            score_percentage=round(score_percentage, 2),
            test_results=test_results,
        )
