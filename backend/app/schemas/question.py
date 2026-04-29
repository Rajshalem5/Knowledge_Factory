# app/schemas/question.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class QuestionCreate(BaseModel):
    qid: str
    title: str
    description: str
    difficulty: str
    topics: List[str]
    input_format: str
    output_format: str
    constraints: str
    boilerplate: Dict[str, Any]
    public_test_cases: Dict[str, Any]
    private_test_cases: Dict[str, Any]
    generated_by_ai: bool = False
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None


class QuestionResponse(BaseModel):
    id: str
    qid: str
    title: str
    difficulty: str
    topics: List[str]
    is_active: bool
