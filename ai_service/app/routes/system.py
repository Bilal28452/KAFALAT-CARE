from flask import Blueprint, jsonify

bp = Blueprint("system", __name__)


@bp.get("/health")
def health():
    """The backend calls this to check that the AI service is alive."""
    return jsonify(status="ok", service="kafalatcare-ai")
