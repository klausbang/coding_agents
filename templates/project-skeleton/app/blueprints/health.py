"""IF-001 GET /health: liveness and database connectivity."""
from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        db.session.rollback()
        database = "unavailable"
    status = "ok" if database == "ok" else "degraded"
    return jsonify(status=status, database=database), 200 if status == "ok" else 503
