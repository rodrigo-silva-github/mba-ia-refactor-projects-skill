from flask import Blueprint

from controllers import produto_controller

bp = Blueprint("produtos", __name__)

bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar, methods=["GET"])
bp.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar_por_id, methods=["GET"])
bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar, methods=["PUT"])
bp.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar, methods=["DELETE"])
