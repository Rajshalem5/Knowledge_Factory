"""Unit tests for domain enums (CandidateStatus, Role, AssessmentRound, etc.)."""
import pytest
from app.core.enums import (
    CandidateStatus,
    Role,
    UserStatus,
    CycleStatus,
    AssessmentRound,
    AssessmentStatus,
    SubmissionSection,
    ScoreVerdict,
    InterviewRecommendation,
    ProctoringEventType,
    ProctoringSeverity,
)


class TestCandidateStatus:
    """Test CandidateStatus enum, display_status mapping, and from_display_status."""

    def test_display_status_applied(self):
        """Test: APPLIED maps to 'applied'."""
        assert CandidateStatus.APPLIED.display_status == "applied"

    def test_display_status_eligible(self):
        """Test: ROUND1_PASSED maps to 'eligible'."""
        assert CandidateStatus.ROUND1_PASSED.display_status == "eligible"

    def test_display_status_round1(self):
        """Test: ROUND2_IN_PROGRESS and ROUND2_PASSED map to 'round1'."""
        assert CandidateStatus.ROUND2_IN_PROGRESS.display_status == "round1"
        assert CandidateStatus.ROUND2_PASSED.display_status == "round1"

    def test_display_status_round2(self):
        """Test: ROUND3_IN_PROGRESS and ROUND3_PASSED map to 'round2'."""
        assert CandidateStatus.ROUND3_IN_PROGRESS.display_status == "round2"
        assert CandidateStatus.ROUND3_PASSED.display_status == "round2"

    def test_display_status_round3(self):
        """Test: INTERVIEW_SCHEDULED maps to 'round3'."""
        assert CandidateStatus.INTERVIEW_SCHEDULED.display_status == "round3"

    def test_display_status_interviewed(self):
        """Test: INTERVIEW_COMPLETED maps to 'interviewed'."""
        assert CandidateStatus.INTERVIEW_COMPLETED.display_status == "interviewed"

    def test_display_status_selected(self):
        """Test: SELECTED maps to 'selected'."""
        assert CandidateStatus.SELECTED.display_status == "selected"

    def test_display_status_rejected(self):
        """Test: Various rejection/terminal statuses map to 'rejected'."""
        assert CandidateStatus.ROUND1_REJECTED.display_status == "rejected"
        assert CandidateStatus.ROUND2_REJECTED.display_status == "rejected"
        assert CandidateStatus.ROUND3_REJECTED.display_status == "rejected"
        assert CandidateStatus.FINAL_REJECTED.display_status == "rejected"
        assert CandidateStatus.TERMINATED.display_status == "rejected"

    def test_from_display_status_applied(self):
        """Test: 'applied' maps to APPLIED."""
        assert CandidateStatus.from_display_status("applied") == CandidateStatus.APPLIED

    def test_from_display_status_eligible(self):
        """Test: 'eligible' maps to ROUND1_PASSED."""
        assert CandidateStatus.from_display_status("eligible") == CandidateStatus.ROUND1_PASSED

    def test_from_display_status_round1(self):
        """Test: 'round1' maps to ROUND2_IN_PROGRESS."""
        assert CandidateStatus.from_display_status("round1") == CandidateStatus.ROUND2_IN_PROGRESS

    def test_from_display_status_round2(self):
        """Test: 'round2' maps to ROUND3_IN_PROGRESS."""
        assert CandidateStatus.from_display_status("round2") == CandidateStatus.ROUND3_IN_PROGRESS

    def test_from_display_status_round3(self):
        """Test: 'round3' maps to INTERVIEW_SCHEDULED."""
        assert CandidateStatus.from_display_status("round3") == CandidateStatus.INTERVIEW_SCHEDULED

    def test_from_display_status_interviewed(self):
        """Test: 'interviewed' maps to INTERVIEW_COMPLETED."""
        assert CandidateStatus.from_display_status("interviewed") == CandidateStatus.INTERVIEW_COMPLETED

    def test_from_display_status_selected(self):
        """Test: 'selected' maps to SELECTED."""
        assert CandidateStatus.from_display_status("selected") == CandidateStatus.SELECTED

    def test_from_display_status_rejected(self):
        """Test: 'rejected' maps to FINAL_REJECTED."""
        assert CandidateStatus.from_display_status("rejected") == CandidateStatus.FINAL_REJECTED

    def test_from_display_status_case_insensitive(self):
        """Test: display_status lookup is case-insensitive."""
        assert CandidateStatus.from_display_status("ELIGIBLE") == CandidateStatus.ROUND1_PASSED
        assert CandidateStatus.from_display_status("Round1") == CandidateStatus.ROUND2_IN_PROGRESS
        assert CandidateStatus.from_display_status("SELECTED") == CandidateStatus.SELECTED

    def test_from_display_status_invalid(self):
        """Test: invalid display status returns None."""
        assert CandidateStatus.from_display_status("nonexistent") is None
        assert CandidateStatus.from_display_status("") is None
        assert CandidateStatus.from_display_status("unknown") is None

    def test_round_trip_display_status(self):
        """Test: display_status -> from_display_status round trip for each status."""
        for status in CandidateStatus:
            display = status.display_status
            mapped = CandidateStatus.from_display_status(display)
            # Round trip should give us a valid status (not necessarily the same one,
            # since multiple statuses map to the same display_status)
            assert mapped is not None
            # Verify the display status is consistent
            assert mapped.display_status == display


class TestRole:
    """Test Role enum values."""

    def test_role_values(self):
        """Test: Role enum has expected members."""
        assert Role.SUPERADMIN.value == "SUPERADMIN"
        assert Role.ADMIN.value == "ADMIN"
        assert Role.HR.value == "HR"
        assert Role.INTERVIEWER.value == "INTERVIEWER"

    def test_role_string_coercion(self):
        """Test: Role values can be compared with strings."""
        assert Role("SUPERADMIN") == Role.SUPERADMIN
        assert Role("ADMIN") == Role.ADMIN
        assert Role("HR") == Role.HR
        assert Role("INTERVIEWER") == Role.INTERVIEWER


class TestUserStatus:
    """Test UserStatus enum values."""

    def test_user_status_values(self):
        """Test: UserStatus enum has expected members."""
        assert UserStatus.ACTIVE.value == "ACTIVE"
        assert UserStatus.INACTIVE.value == "INACTIVE"
        assert UserStatus.PENDING.value == "PENDING"


class TestCycleStatus:
    """Test CycleStatus enum values."""

    def test_cycle_status_values(self):
        """Test: CycleStatus enum has expected members."""
        assert CycleStatus.DRAFT.value == "DRAFT"
        assert CycleStatus.ACTIVE.value == "ACTIVE"
        assert CycleStatus.CLOSED.value == "CLOSED"


class TestAssessmentRound:
    """Test AssessmentRound enum values."""

    def test_assessment_round_values(self):
        """Test: AssessmentRound has ROUND_2 and ROUND_3."""
        assert AssessmentRound.ROUND_2.value == "ROUND_2"
        assert AssessmentRound.ROUND_3.value == "ROUND_3"


class TestAssessmentStatus:
    """Test AssessmentStatus enum values."""

    def test_assessment_status_values(self):
        """Test: AssessmentStatus has expected lifecycle states."""
        assert AssessmentStatus.NOT_STARTED.value == "NOT_STARTED"
        assert AssessmentStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert AssessmentStatus.COMPLETED.value == "COMPLETED"
        assert AssessmentStatus.TERMINATED.value == "TERMINATED"


class TestSubmissionSection:
    """Test SubmissionSection enum values."""

    def test_submission_section_values(self):
        """Test: SubmissionSection has CODING, MCQ, USECASE."""
        assert SubmissionSection.CODING.value == "CODING"
        assert SubmissionSection.MCQ.value == "MCQ"
        assert SubmissionSection.USECASE.value == "USECASE"


class TestScoreVerdict:
    """Test ScoreVerdict enum values."""

    def test_score_verdict_values(self):
        """Test: ScoreVerdict has PASS and FAIL."""
        assert ScoreVerdict.PASS.value == "PASS"
        assert ScoreVerdict.FAIL.value == "FAIL"


class TestInterviewRecommendation:
    """Test InterviewRecommendation enum values."""

    def test_interview_recommendation_values(self):
        """Test: InterviewRecommendation has SELECT, REJECT, HOLD."""
        assert InterviewRecommendation.SELECT.value == "SELECT"
        assert InterviewRecommendation.REJECT.value == "REJECT"
        assert InterviewRecommendation.HOLD.value == "HOLD"


class TestProctoringEventType:
    """Test ProctoringEventType enum values."""

    def test_proctoring_event_type_values(self):
        """Test: ProctoringEventType has expected violation types."""
        assert ProctoringEventType.TAB_SWITCH.value == "tab_switch"
        assert ProctoringEventType.FACE_NOT_DETECTED.value == "face_not_detected"
        assert ProctoringEventType.MULTIPLE_FACES.value == "multiple_faces"
        assert ProctoringEventType.COPY_PASTE.value == "copy_paste"
        assert ProctoringEventType.PHONE_DETECTED.value == "phone_detected"
        assert ProctoringEventType.RIGHT_CLICK.value == "right_click"


class TestProctoringSeverity:
    """Test ProctoringSeverity enum values."""

    def test_proctoring_severity_values(self):
        """Test: ProctoringSeverity has LOW, MEDIUM, HIGH."""
        assert ProctoringSeverity.LOW.value == "low"
        assert ProctoringSeverity.MEDIUM.value == "medium"
        assert ProctoringSeverity.HIGH.value == "high"
