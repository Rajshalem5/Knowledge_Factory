"""Question schemas — public vs private test cases."""

from typing import Optional
from pydantic import BaseModel


class TestCase(BaseModel):
    input: str
    expected_output: str
    is_public: bool = True          # public → shown to candidate; private → hidden


class Question(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str                 # easy | medium | hard
    boilerplate: dict[str, str]     # { "python": "...", "java": "...", "cpp": "..." }
    public_test_cases: list[TestCase]   # shown on assessment page
    private_test_cases: list[TestCase]  # used only for evaluation scoring


class QuestionGenerationRequest(BaseModel):
    topic: str = "data structures and algorithms"
    difficulty: str = "medium"
    num_public_cases: int = 2
    num_private_cases: int = 4


class QuestionPublicView(BaseModel):
    """What the frontend receives — NO private test cases."""
    id: str
    title: str
    description: str
    difficulty: str
    boilerplate: dict[str, str]
    public_test_cases: list[TestCase]
