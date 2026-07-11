from flask import Blueprint

from controllers import admin_controller
from middlewares.auth import requer_chave_admin

bp = Blueprint("admin", __name__)

bp.add_url_rule(
    "/admin/reset-db",
    "reset_database",
    requer_chave_admin(admin_controller.reset_database),
    methods=["POST"],
)
