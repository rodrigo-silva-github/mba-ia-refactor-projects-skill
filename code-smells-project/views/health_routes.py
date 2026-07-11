from flask import Blueprint

from controllers import health_controller

bp = Blueprint("health", __name__)

bp.add_url_rule("/health", "health_check", health_controller.health_check, methods=["GET"])
