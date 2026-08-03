from __future__ import annotations

from dataclasses import dataclass

from .models import ErrorKind


class DropFixBaseError(Exception):
    """Base class for predictable error handling."""

    status_code: int = 400

    def __init__(self, code: ErrorKind, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_payload(self) -> dict:
        return {"code": self.code.value, "message": self.message, "details": self.details}


class ValidationError(DropFixBaseError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(ErrorKind.VALIDATION, message, details)


class InsufficientDataError(ValidationError):
    status_code = 422

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, {"insufficient": True, **(details or {})})
        self.code = ErrorKind.INSUFFICIENT_DATA


class UnsupportedFormatError(DropFixBaseError):
    status_code = 415

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(ErrorKind.UNSUPPORTED_FORMAT, message, details)


class InsufficientDataError(DropFixBaseError):
    status_code = 422

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(ErrorKind.INSUFFICIENT_DATA, message, details)


class ProcessingTimeoutError(DropFixBaseError):
    status_code = 408

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(ErrorKind.PROCESSING_TIMEOUT, message, details)


class DependencyFailureError(DropFixBaseError):
    status_code = 503

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(ErrorKind.DEPENDENCY_FAILURE, message, details)
