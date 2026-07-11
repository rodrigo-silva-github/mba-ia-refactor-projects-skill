from functools import wraps

from flask import abort, jsonify, request

from config import settings


def requer_chave_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            abort(404)
        chave = request.headers.get("X-Admin-Key")
        if not chave or chave != settings.ADMIN_RESET_KEY:
            return jsonify({"erro": "Não autorizado", "sucesso": False}), 401
        return f(*args, **kwargs)

    return wrapper
