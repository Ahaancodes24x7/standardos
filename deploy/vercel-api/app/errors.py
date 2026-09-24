from __future__ import annotations


class AppError(Exception):
    """An error whose message is safe to show to the user."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFound(AppError):
    def __init__(self, message: str = "Not found.") -> None:
        super().__init__(message, 404)


class Unauthorized(AppError):
    def __init__(self, message: str = "Your session expired. Please sign in again.") -> None:
        super().__init__(message, 401)
