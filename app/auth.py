import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_api_key(fn):
    """Only our backend may call the AI service, not browsers or outside clients."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("AI_SERVICE_API_KEY", "")
        if expected:  # enforce the key when one is configured
            given = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(given, expected):
                return jsonify(error="unauthorized", message="Invalid API key"), 401
        return fn(*args, **kwargs)

    return wrapper
