from fastapi import status


class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "app_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, code="not_found")


class DependencyError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="dependency_error")


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="validation_error")


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, code="authentication_error")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, code="conflict_error")
