import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def registrar_error_handlers(app):
    @app.errorhandler(Exception)
    def tratar_erro(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception("erro_nao_tratado")
        return jsonify({"erro": "Erro interno no servidor", "sucesso": False}), 500
