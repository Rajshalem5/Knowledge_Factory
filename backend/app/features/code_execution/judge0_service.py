"""Code execution service using Judge0 CE (Community Edition)."""

import httpx
import base64
from typing import Optional
from app.features.code_execution.schemas import (
    CodeExecutionResponse,
    TestCase,
    EvaluationResult,
)


class Judge0ExecutionService:
    """Service for executing code using Judge0 CE API."""
    
    # Judge0 CE public endpoint (free, no auth required)
    JUDGE0_URL = "https://judge0-ce.p.rapidapi.com"
    
    # Language ID mapping for Judge0
    LANGUAGE_IDS = {
        "python": 71,      # Python 3.8.1
        "java": 62,        # Java (OpenJDK 13.0.1)
        "cpp": 54,         # C++ (GCC 9.2.0)
        "c++": 54,
        "javascript": 63,  # JavaScript (Node.js 12.14.0)
        "c": 50,          # C (GCC 9.2.0)
    }
    
    EXECUTION_TIMEOUT = 10.0
    
    async def execute_code(
        self, 
        language: str, 
        code: str, 
        stdin: str = ""
    ) -> CodeExecutionResponse:
        """Execute code using Judge0 CE API."""
        language = language.lower()
        if language == "c++":
            language = "cpp"
        
        language_id = self.LANGUAGE_IDS.get(language, 71)
        
        # Encode source code and stdin to base64
        source_code_b64 = base64.b64encode(code.encode()).decode()
        stdin_b64 = base64.b64encode(stdin.encode()).decode() if stdin else ""
        
        # Create submission
        payload = {
            "source_code": source_code_b64,
            "language_id": language_id,
            "stdin": stdin_b64,
            "base64_encoded": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.EXECUTION_TIMEOUT) as client:
                # Submit code
                response = await client.post(
                    f"{self.JUDGE0_URL}/submissions?base64_encoded=true&wait=true",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Decode results
                stdout = ""
                stderr = ""
                
                if data.get("stdout"):
                    stdout = base64.b64decode(data["stdout"]).decode()
                
                if data.get("stderr"):
                    stderr = base64.b64decode(data["stderr"]).decode()
                
                if data.get("compile_output"):
                    compile_output = base64.b64decode(data["compile_output"]).decode()
                    if compile_output:
                        return CodeExecutionResponse(
                            status="COMPILE_ERROR",
                            stdout=stdout,
                            stderr=compile_output,
                            exit_code=data.get("status", {}).get("id"),
                        )
                
                # Check status
                status_id = data.get("status", {}).get("id")
                
                if status_id == 3:  # Accepted
                    return CodeExecutionResponse(
                        status="SUCCESS",
                        stdout=stdout,
                        stderr=stderr,
                        exit_code=0,
                    )
                elif status_id in [5, 6]:  # Time Limit Exceeded
                    return CodeExecutionResponse(
                        status="TIMEOUT",
                        stdout=stdout,
                        stderr="Time limit exceeded",
                        exit_code=-1,
                    )
                else:  # Runtime error or other
                    return CodeExecutionResponse(
                        status="RUNTIME_ERROR",
                        stdout=stdout,
                        stderr=stderr or data.get("status", {}).get("description", "Runtime error"),
                        exit_code=status_id,
                    )
                
        except httpx.TimeoutException:
            return CodeExecutionResponse(
                status="TIMEOUT",
                stdout="",
                stderr="Execution timed out",
                exit_code=-1,
            )
        except Exception as e:
            return CodeExecutionResponse(
                status="RUNTIME_ERROR",
                stdout="",
                stderr=f"Error: {str(e)}",
                exit_code=-1,
            )
    
    async def evaluate_code(
        self,
        language: str,
        code: str,
        test_cases: list[TestCase]
    ) -> EvaluationResult:
        """Evaluate code against multiple test cases."""
        passed = 0
        failed = 0
        test_results = []
        
        for idx, test_case in enumerate(test_cases, 1):
            result = await self.execute_code(language, code, test_case.input)
            
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
