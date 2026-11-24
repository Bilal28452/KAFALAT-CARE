from flask import Flask, jsonify

from .config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    from .routes.system import bp as system_bp
    from .routes.health_pattern import bp as health_pattern_bp

    app.register_blueprint(system_bp)
    app.register_blueprint(health_pattern_bp)

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="not_found", message="Endpoint does not exist"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify(error="server_error", message="The AI service encountered an error"), 500

    return app
