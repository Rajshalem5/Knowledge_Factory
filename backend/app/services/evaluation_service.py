from abc import ABC, abstractmethod
from typing import Dict, List
from .judge0_client import judge0_client


class ScoreResult:
    """Evaluation result container"""
    
    def __init__(
        self,
        correctness: float,
        mcq_score: int,
        weighted_total: float,
        verdict: str,
        details: Dict = None
    ):
        self.correctness = correctness
        self.mcq_score = mcq_score
        self.weighted_total = weighted_total
        self.verdict = verdict
        self.details = details or {}


class EvaluationService(ABC):
    """Abstract evaluation service interface for Phase 1 and Phase 2"""
    
    @abstractmethod
    async def evaluate(
        self,
        coding_submissions: List[Dict],
        mcq_answers: Dict[str, str],
        questions: Dict
    ) -> ScoreResult:
        """
        Evaluate assessment submission
        
        Args:
            coding_submissions: List of coding problem submissions
            mcq_answers: MCQ answers dict
            questions: Original questions from assessment
            
        Returns:
            ScoreResult object
        """
        pass


class Judge0Evaluator(EvaluationService):
    """Phase 1: Judge0-based evaluation only"""
    
    def __init__(self, coding_weight: float = 0.7, mcq_points: int = 3, pass_threshold: float = 70.0):
        self.coding_weight = coding_weight
        self.mcq_points = mcq_points
        self.pass_threshold = pass_threshold
    
    async def evaluate(
        self,
        coding_submissions: List[Dict],
        mcq_answers: Dict[str, str],
        questions: Dict
    ) -> ScoreResult:
        """Evaluate using Judge0 correctness only"""
        
        # Evaluate coding problems
        coding_results = await self._evaluate_coding(coding_submissions, questions["coding"])
        
        # Evaluate MCQs
        mcq_score = self._evaluate_mcq(mcq_answers, questions["mcq"])
        
        # Calculate final score
        avg_correctness = sum(r["percentage"] for r in coding_results) / len(coding_results) if coding_results else 0
        weighted_total = (avg_correctness * self.coding_weight) + (mcq_score * self.mcq_points)
        
        verdict = "PASS" if weighted_total >= self.pass_threshold else "FAIL"
        
        return ScoreResult(
            correctness=avg_correctness,
            mcq_score=mcq_score,
            weighted_total=weighted_total,
            verdict=verdict,
            details={
                "coding_results": coding_results,
                "mcq_correct": mcq_score,
                "mcq_total": len(questions["mcq"])
            }
        )
    
    async def _evaluate_coding(self, submissions: List[Dict], coding_questions: List[Dict]) -> List[Dict]:
        """Evaluate coding submissions against hidden test cases"""
        results = []
        
        # Create question lookup
        question_map = {q["id"]: q for q in coding_questions}
        
        for submission in submissions:
            question_id = submission["question_id"]
            question = question_map.get(question_id)
            
            if not question:
                results.append({
                    "question_id": question_id,
                    "passed": 0,
                    "total": 0,
                    "percentage": 0,
                    "error": "Question not found"
                })
                continue
            
            # Run against hidden test cases
            test_result = await judge0_client.run_test_cases(
                code=submission["code"],
                language=submission["language"],
                test_cases=question["hidden_test_cases"]
            )
            
            results.append({
                "question_id": question_id,
                "passed": test_result["passed"],
                "total": test_result["total"],
                "percentage": test_result["percentage"],
                "details": test_result["details"]
            })
        
        return results
    
    def _evaluate_mcq(self, answers: Dict[str, str], mcq_questions: List[Dict]) -> int:
        """Evaluate MCQ answers"""
        correct = 0
        question_map = {q["id"]: q for q in mcq_questions}
        
        for question_id, answer in answers.items():
            question = question_map.get(question_id)
            if question and question["correct_answer"] == answer:
                correct += 1
        
        return correct


class AIEvaluator(EvaluationService):
    """
    Phase 2: AI-based evaluation (INTERFACE ONLY - NOT IMPLEMENTED)
    
    This will be implemented in Phase 2 to add:
    - Code quality analysis
    - Efficiency evaluation
    - Edge case handling
    - Best practices check
    """
    
    async def evaluate(
        self,
        coding_submissions: List[Dict],
        mcq_answers: Dict[str, str],
        questions: Dict
    ) -> ScoreResult:
        raise NotImplementedError("AI evaluation will be implemented in Phase 2")


# Factory function to get evaluator
def get_evaluator(phase: str = "phase1") -> EvaluationService:
    """Get appropriate evaluator based on phase"""
    if phase == "phase1":
        return Judge0Evaluator()
    elif phase == "phase2":
        return AIEvaluator()
    else:
        raise ValueError(f"Unknown phase: {phase}")
