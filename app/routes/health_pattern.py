from flask import Blueprint, jsonify, request

from ..auth import require_api_key
from ..services.health_rules import ValidationError, analyze_health_records

bp = Blueprint("health_pattern", __name__)


@bp.post("/health-pattern")
@require_api_key
def health_pattern():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify(error="bad_request", message="A JSON body is required"), 400
    try:
        result = analyze_health_records(payload)
    except ValidationError as e:
        return jsonify(error="validation_error", message=str(e)), 400
    return jsonify(result)
