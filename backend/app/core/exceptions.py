"""
Custom exception hierarchy for the Knowledge Factory backend.

These exceptions are raised in the service layer and caught by FastAPI
exception handlers to produce consistent JSON error responses matching
the envelope defined in the architecture doc Section 6.6:

    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "CGPA must be between 0 and 10",
            "field": "cgpa",
            "request_id": "req_01HXYZ...",
            "timestamp": "2026-04-16T10:12:00Z"
        }
    }
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        message: str = "An unexpected error occurred",
        field: str | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.field = field
        # Pass a consistent detail to FastAPI's HTTPException
        super().__init__(status_code=status_code, detail=message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", resource_id: str | None = None) -> None:
        identifier = f" {resource_id}" if resource_id else ""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=f"{resource}{identifier} not found",
        )


class ConflictError(AppException):
    """Raised on duplicate resource creation or state conflicts."""

    def __init__(self, message: str = "Resource already exists", field: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message=message,
            field=field,
        )


class ValidationError(AppException):
    """Raised for business-rule validation failures (not Pydantic validation)."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message=message,
            field=field,
        )


class UnauthorizedError(AppException):
    """Raised when authentication fails or is missing."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            message=message,
        )


class ForbiddenError(AppException):
    """Raised when the authenticated user lacks the required role/permission."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            message=message,
        )


class InvalidStateTransitionError(AppException):
    """
    Raised when a candidate status transition violates the state machine.

    The architecture doc Section 12 defines a strict FSM. Any attempt
    to jump states (e.g. applied → interviewed) raises this.
    """

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="INVALID_STATE_TRANSITION",
            message=f"Cannot transition from '{from_status}' to '{to_status}'",
            field="status",
        )


class RateLimitExceededError(AppException):
    """Raised when a rate limit is breached."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
        )


class AISpendCapExceededError(AppException):
    """Raised when the per-cycle AI spend cap is reached."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="AI_SPEND_CAP_EXCEEDED",
            message="AI spending cap for this hiring cycle has been reached",
        )


class ProctoringTerminationError(AppException):
    """Raised when proctoring violations trigger assessment termination."""

    def __init__(self, reason: str = "Proctoring policy violation") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PROCTORING_TERMINATION",
            message=reason,
        )
