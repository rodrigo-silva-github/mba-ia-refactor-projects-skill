from flask import Blueprint

from controllers import usuario_controller

bp = Blueprint("usuarios", __name__)

bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar, methods=["GET"])
bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_por_id, methods=["GET"])
bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar, methods=["POST"])
bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
