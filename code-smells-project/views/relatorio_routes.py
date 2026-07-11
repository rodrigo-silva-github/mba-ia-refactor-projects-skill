from flask import Blueprint

from controllers import relatorio_controller

bp = Blueprint("relatorios", __name__)

bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.vendas, methods=["GET"])
