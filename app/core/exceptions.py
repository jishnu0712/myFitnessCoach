"""Define safe, domain-oriented exceptions used by API and service layers."""


class AppException(Exception):
    """Base exception carrying an HTTP status and stable public error code."""

    status_code = 500
    code = "APPLICATION_ERROR"

    def __init__(self, message: str, details: object | None = None) -> None:
        """Store the client-safe message and optional non-sensitive details."""
        super().__init__(message)
        self.message = message
        self.details = details


class BadRequestException(AppException):
    """Represent a request that is syntactically valid but cannot be accepted."""

    status_code = 400
    code = "BAD_REQUEST"


class UnauthorizedException(AppException):
    """Represent a request that requires valid authentication credentials."""

    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenException(AppException):
    """Represent an authenticated request lacking required permissions."""

    status_code = 403
    code = "FORBIDDEN"


class NotFoundException(AppException):
    """Represent a requested resource that does not exist."""

    status_code = 404
    code = "RESOURCE_NOT_FOUND"


class ServiceUnavailableException(AppException):
    """Represent a temporarily unavailable dependency such as PostgreSQL."""

    status_code = 503
    code = "SERVICE_UNAVAILABLE"
