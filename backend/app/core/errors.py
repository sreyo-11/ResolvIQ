class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class InvalidTransitionError(AppError):
    status_code = 409
    code = "invalid_status_transition"

class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"


class UpstreamError(AppError):
    status_code = 502
    code = "upstream_error"