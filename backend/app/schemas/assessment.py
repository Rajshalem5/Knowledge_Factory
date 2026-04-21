from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class TestCase(BaseModel):
    input: str
    output: str


class CodingProblem(BaseModel):
    id: str
    title: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    boilerplate: Dict[str, str]
    visible_test_cases: List[TestCase]
    hidden_test_cases: List[TestCase]


class MCQOption(BaseModel):
    id: str
    text: str


class MCQQuestion(BaseModel):
    id: str
    question: str
    options: List[MCQOption]
    correct_answer: str


class AssessmentStartResponse(BaseModel):
    assessment_id: int
    candidate_id: int
    duration_minutes: int
    started_at: datetime


class MonacoCodingProblem(BaseModel):
    id: str
    title: str
    description: str
    boilerplate: str
    visible_test_cases: List[TestCase]
    default_language: str = "python"


class MonacoMCQ(BaseModel):
    id: str
    question: str
    options: List[MCQOption]


class AssessmentQuestionsResponse(BaseModel):
    coding: List[MonacoCodingProblem]
    mcq: List[MonacoMCQ]


class CodeExecuteRequest(BaseModel):
    code: str
    language: str
    stdin: str = ""


class CodeExecuteResponse(BaseModel):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    status: str
    time: Optional[str] = None
    memory: Optional[str] = None


class CodingSubmission(BaseModel):
    question_id: str
    code: str
    language: str


class AssessmentSubmitRequest(BaseModel):
    coding: List[CodingSubmission]
    mcq_answers: Dict[str, str]


class AssessmentResultResponse(BaseModel):
    total_score: float
    coding_score: float
    mcq_score: int
    verdict: str
    evaluation_details: Optional[Dict] = None
