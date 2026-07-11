from flask import Blueprint

from controllers import pedido_controller

bp = Blueprint("pedidos", __name__)

bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar, methods=["POST"])
bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos, methods=["GET"])
bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_pedidos_usuario",
    pedido_controller.listar_por_usuario,
    methods=["GET"],
)
bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status_pedido",
    pedido_controller.atualizar_status,
    methods=["PUT"],
)
