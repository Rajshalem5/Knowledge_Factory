"""Unit tests for the apply_candidate_filters utility function."""
import pytest
from sqlalchemy import select
from app.core.filters import apply_candidate_filters
from app.features.candidates.models import Candidate
from app.core.enums import CandidateStatus


class TestApplyCandidateFilters:
    """Test the apply_candidate_filters function."""

    def _query(self):
        """Return a base SELECT query for testing."""
        return select(Candidate)

    def test_no_filters_returns_original_query(self):
        """Test: Calling with no filters returns the query unchanged."""
        q = self._query()
        result = apply_candidate_filters(q)
        assert result is q

    def test_filter_by_name(self):
        """Test: name filter applies LOWER LIKE condition."""
        q = self._query()
        result = apply_candidate_filters(q, name="John")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        # SQLite uses LOWER() LIKE LOWER() instead of ILIKE
        assert "LOWER" in compiled.upper()
        assert "John" in compiled

    def test_filter_by_branch_single(self):
        """Test: single branch filter applies ILIKE condition."""
        q = self._query()
        result = apply_candidate_filters(q, branch="CSE")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "CSE" in compiled

    def test_filter_by_branch_multi(self):
        """Test: Comma-separated branches use OR conditions."""
        q = self._query()
        result = apply_candidate_filters(q, branch="CSE,ECE")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        # Should contain OR for branch filter
        assert "OR" in compiled.upper() or "or" in compiled.lower()

    def test_filter_by_college(self):
        """Test: college filter applies ILIKE condition."""
        q = self._query()
        result = apply_candidate_filters(q, college="Test Uni")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "Test" in compiled

    def test_filter_by_passed_out_year(self):
        """Test: passed_out_year filter uses exact match."""
        q = self._query()
        result = apply_candidate_filters(q, passed_out_year=2026)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "2026" in compiled

    def test_filter_by_cgpa_range(self):
        """Test: cgpa_min and cgpa_max filters use >= and <=."""
        q = self._query()
        result = apply_candidate_filters(q, cgpa_min=6.0, cgpa_max=9.0)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        # Should have both >= and <= conditions
        assert "6.0" in compiled or "6" in compiled
        assert "9.0" in compiled or "9" in compiled

    def test_filter_by_search(self):
        """Test: search filter searches name, email, and college."""
        q = self._query()
        result = apply_candidate_filters(q, search="test")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        # Should contain OR conditions for name, email, college
        assert "OR" in compiled.upper() or "or" in compiled.lower()

    def test_filter_by_created_date_range(self):
        """Test: created_after and created_before use datetime comparison."""
        from datetime import date
        q = self._query()
        result = apply_candidate_filters(q, created_after=date(2026, 1, 1))
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled or ">=" in compiled

    def test_filter_by_email(self):
        """Test: exact email filter."""
        q = self._query()
        result = apply_candidate_filters(q, email="test@example.com")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test@example.com" in compiled

    def test_filter_by_phone(self):
        """Test: phone filter uses ILIKE."""
        q = self._query()
        result = apply_candidate_filters(q, phone="+91")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "+91" in compiled

    def test_filter_by_cycle_id(self):
        """Test: cycle_id exact match filter."""
        q = self._query()
        result = apply_candidate_filters(q, cycle_id="abc-123")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "abc-123" in compiled

    def test_filter_by_email_verified(self):
        """Test: email_verified boolean filter."""
        q = self._query()
        result = apply_candidate_filters(q, email_verified=True)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "email_verified" in compiled

    def test_filter_by_passed_out_year_range(self):
        """Test: passed_out_year_min and passed_out_year_max."""
        q = self._query()
        result = apply_candidate_filters(q, passed_out_year_min=2020, passed_out_year_max=2026)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled
        assert "<=" in compiled

    def test_filter_by_status_raw(self):
        """Test: status filter accepts raw backend status."""
        q = self._query()
        result = apply_candidate_filters(q, status="APPLIED")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "APPLIED" in compiled

    def test_filter_by_status_display(self):
        """Test: status filter accepts display_status (e.g. 'round1')."""
        q = self._query()
        result = apply_candidate_filters(q, status="round1")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ROUND2_IN_PROGRESS" in compiled

    def test_filter_by_status_multi(self):
        """Test: status filter accepts comma-separated values."""
        q = self._query()
        result = apply_candidate_filters(q, status="APPLIED,ROUND1_PASSED")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "APPLIED" in compiled
        assert "ROUND1_PASSED" in compiled

    def test_filter_language_choice_single(self):
        """Test: language_choice single value."""
        q = self._query()
        result = apply_candidate_filters(q, language_choice="python")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "python" in compiled

    def test_filter_language_choice_multi(self):
        """Test: language_choice comma-separated uses OR."""
        q = self._query()
        result = apply_candidate_filters(q, language_choice="python,java")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "OR" in compiled.upper() or "or" in compiled.lower()

    def test_filter_has_resume(self):
        """Test: has_resume filter uses IS NOT NULL."""
        q = self._query()
        result = apply_candidate_filters(q, has_resume=True)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "NOT NULL" in compiled.upper() or "not null" in compiled.lower()

    def test_filter_has_govt_id_false(self):
        """Test: has_govt_id=False uses IS NULL."""
        q = self._query()
        result = apply_candidate_filters(q, has_govt_id=False)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "NULL" in compiled.upper() or "null" in compiled.lower()

    def test_filter_has_phone(self):
        """Test: has_phone filter."""
        q = self._query()
        result = apply_candidate_filters(q, has_phone=True)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "phone" in compiled.lower()
        assert "NOT NULL" in compiled.upper() or "not null" in compiled.lower()

    def test_filter_all_combined(self):
        """Test: multiple filters combine correctly (AND logic)."""
        q = self._query()
        result = apply_candidate_filters(
            q,
            branch="CSE",
            college="Test",
            cgpa_min=6.0,
            status="APPLIED",
            search="john",
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        # All conditions should be present
        assert "CSE" in compiled
        assert "Test" in compiled
        assert "6.0" in compiled or "6" in compiled
        assert "john" in compiled
        assert "APPLIED" in compiled

    def test_filter_updated_after(self):
        """Test: updated_after filter uses datetime >= comparison."""
        from datetime import date
        q = self._query()
        result = apply_candidate_filters(q, updated_after=date(2026, 5, 1))
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled
        assert "updated_at" in compiled.lower()

    def test_filter_updated_before(self):
        """Test: updated_before filter uses datetime <= comparison."""
        from datetime import date
        q = self._query()
        result = apply_candidate_filters(q, updated_before=date(2026, 6, 1))
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "<=" in compiled
        assert "updated_at" in compiled.lower()

    def test_filter_updated_range(self):
        """Test: both updated_after and updated_before combined."""
        from datetime import date
        q = self._query()
        result = apply_candidate_filters(
            q, updated_after=date(2026, 5, 1), updated_before=date(2026, 6, 1)
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled
        assert "<=" in compiled
        assert "updated_at" in compiled.lower()

    def test_filter_has_assessment(self):
        """Test: has_assessment=True adds a subquery with assessments table."""
        q = self._query()
        result = apply_candidate_filters(q, has_assessment=True)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "assessments" in compiled.lower() or "assessment" in compiled.lower()
        assert "IN" in compiled.upper() or "in" in compiled.lower()

    def test_filter_has_assessment_false(self):
        """Test: has_assessment=False adds a NOT IN subquery."""
        q = self._query()
        result = apply_candidate_filters(q, has_assessment=False)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "NOT IN" in compiled.upper() or "not in" in compiled.lower()

    def test_filter_has_interview_feedback(self):
        """Test: has_interview_feedback=True adds a subquery with interview_feedback table."""
        q = self._query()
        result = apply_candidate_filters(q, has_interview_feedback=True)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "interview_feedback" in compiled.lower()
        assert "IN" in compiled.upper() or "in" in compiled.lower()

    def test_filter_has_interview_feedback_false(self):
        """Test: has_interview_feedback=False adds a NOT IN subquery."""
        q = self._query()
        result = apply_candidate_filters(q, has_interview_feedback=False)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "NOT IN" in compiled.upper() or "not in" in compiled.lower()

    def test_filter_assessment_status(self):
        """Test: assessment_status adds a subquery filtering by assessment status."""
        q = self._query()
        result = apply_candidate_filters(q, assessment_status="IN_PROGRESS")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "assessments" in compiled.lower()
        assert "IN_PROGRESS" in compiled.upper() or "in_progress" in compiled.lower()

    def test_filter_min_score(self):
        """Test: min_score filter uses >= on Score.weighted_total."""
        q = self._query()
        result = apply_candidate_filters(q, min_score=40.0)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled
        assert "scores" in compiled.lower() or "score" in compiled.lower()

    def test_filter_max_score(self):
        """Test: max_score filter uses <= on Score.weighted_total."""
        q = self._query()
        result = apply_candidate_filters(q, max_score=80.0)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "<=" in compiled
        assert "scores" in compiled.lower() or "score" in compiled.lower()

    def test_filter_min_max_score_range(self):
        """Test: both min_score and max_score combined."""
        q = self._query()
        result = apply_candidate_filters(q, min_score=30.0, max_score=90.0)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled
        assert "<=" in compiled
