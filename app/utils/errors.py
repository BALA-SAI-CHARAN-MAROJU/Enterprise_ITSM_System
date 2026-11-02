from flask import jsonify
from werkzeug.exceptions import HTTPException


def api_error(message, status_code=400, code=None):
    payload = {
        "error": {
            "code": code or _default_code(status_code),
            "message": message,
        }
    }
    return jsonify(payload), status_code


def _default_code(status_code):
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        500: "internal_error",
    }
    return mapping.get(status_code, "error")


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        if _wants_json(exc):
            return api_error(exc.description or exc.name, exc.code)
        return exc

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        app.logger.exception("Unhandled error")
        if _request_is_api():
            return api_error("An unexpected error occurred", 500)
        raise exc


def _request_is_api():
    from flask import request

    return request.path.startswith("/api/")


def _wants_json(exc):
    from flask import request

    return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"
