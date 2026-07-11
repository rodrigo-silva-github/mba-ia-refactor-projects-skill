import logging

from flask import jsonify

from database.connection import get_db

logger = logging.getLogger(__name__)


def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("banco_de_dados_resetado")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
