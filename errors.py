from http import HTTPStatus
from typing import Any, Dict, Optional

from flask import jsonify, request
from flask_limiter.errors import RateLimitExceeded
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    error_type = "app_error"

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": {
                "type": self.error_type,
                "message": self.message,
            }
        }
        if self.details is not None:
            payload["error"]["details"] = self.details
        return payload


class ValidationError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_type = "validation_error"


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    error_type = "not_found"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    error_type = "unauthorized"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    error_type = "conflict"


class TooManyRequestsError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_type = "rate_limited"


class InternalServerError(AppError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_type = "internal_error"

    def __init__(self, message: str = "Internal server error", *, details=None):
        super().__init__(message, details=details)


def _extract_validation_message(messages):
    if isinstance(messages, dict):
        for value in messages.values():
            result = _extract_validation_message(value)
            if result:
                return result
    elif isinstance(messages, (list, tuple)):
        for item in messages:
            result = _extract_validation_message(item)
            if result:
                return result
    elif isinstance(messages, str):
        return messages
    return "Invalid input"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        status = err.status_code
        app.logger.warning(
            "handled_app_error",
            extra={
                "event": "handled_app_error",
                "error_type": err.error_type,
                "status": status,
                "path": request.path,
            },
        )
        return jsonify(err.to_dict()), status

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_error(err: MarshmallowValidationError):
        message = _extract_validation_message(err.messages)
        payload = ValidationError(message, details=err.messages)
        return handle_app_error(payload)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        payload = AppError(err.description or "HTTP error")
        payload.status_code = err.code or HTTPStatus.INTERNAL_SERVER_ERROR
        payload.error_type = "http_error"
        return handle_app_error(payload)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(err: RateLimitExceeded):
        payload = TooManyRequestsError(str(err))
        return handle_app_error(payload)

    @app.errorhandler(Exception)
    def handle_generic_exception(err: Exception):
        app.logger.exception(
            "unhandled_exception",
            extra={"event": "unhandled_exception", "path": request.path},
        )
        payload = InternalServerError()
        return jsonify(payload.to_dict()), payload.status_code

