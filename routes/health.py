from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from models import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Простая проверка здоровья приложения и подключения к БД.
    """
    database_status = "healthy"
    http_status = 200

    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error(
            "database_unhealthy",
            extra={"event": "database_health", "error": str(exc)},
        )
        database_status = "unhealthy"
        http_status = 503

    status = "healthy" if database_status == "healthy" else "unhealthy"
    return (
        jsonify(
            {
                "status": status,
                "database": database_status,
                "version": current_app.config.get("APP_VERSION"),
                "environment": current_app.config.get("ENV"),
            }
        ),
        http_status,
    )

