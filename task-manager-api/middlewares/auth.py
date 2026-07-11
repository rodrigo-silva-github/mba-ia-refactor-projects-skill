"""Autenticação/autorização real via token assinado (substitui o fake-jwt-token)."""
from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import settings
from models.user import User

TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)


def generate_token(user_id):
    return _serializer().dumps({'user_id': user_id})


def _decode_token(token):
    try:
        data = _serializer().loads(token, max_age=settings.AUTH_TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get('user_id')


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Autenticação necessária'}), 401

        user_id = _decode_token(auth_header.split(' ', 1)[1])
        if not user_id:
            return jsonify({'error': 'Token inválido ou expirado'}), 401

        user = User.query.get(user_id)
        if not user or not user.active:
            return jsonify({'error': 'Usuário inválido ou inativo'}), 401

        g.current_user = user
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin():
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        return view_func(*args, **kwargs)
    return wrapper
