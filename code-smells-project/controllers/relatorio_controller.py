from flask import jsonify

from models import pedido_model


def vendas():
    relatorio = pedido_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
