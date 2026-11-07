"""Custom exceptions and JSON error handlers.

Every error the API returns has the same shape: {"error": "<message>"}.
"""
from flask import jsonify


class AppError(Exception):
    """Base class for errors that map to an HTTP status code."""

    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    """The client sent invalid input (HTTP 400)."""
    status_code = 400


class NotFoundError(AppError):
    """The requested inventory item does not exist (HTTP 404)."""
    status_code = 404


class ConflictError(AppError):
    """The request conflicts with existing data, e.g. duplicate barcode (HTTP 409)."""
    status_code = 409


class ExternalAPIError(AppError):
    """OpenFoodFacts failed or is unreachable (HTTP 502, or 504 on timeout)."""
    status_code = 502


class ProductNotFoundError(ExternalAPIError):
    """OpenFoodFacts has no matching product (HTTP 404)."""
    status_code = 404


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify({"error": "Method not allowed for this endpoint"}), 405

    @app.errorhandler(500)
    def handle_500(_err):
        return jsonify({"error": "Internal server error"}), 500
