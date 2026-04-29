"""Code execution schemas for Piston integration."""

from typing import Optional
from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    """Request to execute code."""
    language: str = Field(..., description="Programming language (python, java, cpp, javascript)")
    code: str = Field(..., description="Source code to execute")
    stdin: Optional[str] = Field(default="", description="Standard input for the program")


class CodeExecutionResponse(BaseModel):
    """Response from code execution."""
    status: str = Field(..., description="SUCCESS, COMPILE_ERROR, RUNTIME_ERROR, TIMEOUT")
    stdout: Optional[str] = Field(default="", description="Standard output")
    stderr: Optional[str] = Field(default="", description="Standard error")
    exit_code: Optional[int] = Field(default=None, description="Exit code")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")


class TestCase(BaseModel):
    """Single test case for evaluation."""
    input: str = Field(..., description="Input for the test case")
    expected_output: str = Field(..., description="Expected output")


class EvaluationRequest(BaseModel):
    """Request to evaluate code against test cases."""
    language: str
    code: str
    test_cases: list[TestCase]


class EvaluationResult(BaseModel):
    """Result of code evaluation."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    score_percentage: float
    test_results: list[dict]
