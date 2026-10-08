"""Application factory."""
from __future__ import annotations

from flask import Flask

from .config import DEV_SECRET_KEY, get_config
from .extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    if not (app.debug or app.testing) and app.config["SECRET_KEY"] == DEV_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in the environment outside development/testing")

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401  (import models so Alembic sees them)
    from .blueprints.health import bp as health_bp
    from .blueprints.main import bp as main_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp)
    return app
