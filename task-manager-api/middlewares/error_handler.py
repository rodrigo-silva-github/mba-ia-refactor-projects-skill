"""Tratamento de erro centralizado: log completo no servidor, mensagem genérica ao cliente."""
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('erro_nao_tratado')
        return jsonify({'error': 'Erro interno no servidor'}), 500
