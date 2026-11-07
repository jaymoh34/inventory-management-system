"""Flask application factory."""
from flask import Flask

from app.errors import register_error_handlers
from app.routes import bp
from app.store import InventoryStore


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["STORE"] = InventoryStore()
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(bp)
    register_error_handlers(app)
    return app
