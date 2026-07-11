"""Configuração centralizada, lida de variáveis de ambiente (nunca hardcoded)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
DEBUG = _env_bool('FLASK_DEBUG', default=False)
HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
PORT = int(os.environ.get('FLASK_PORT', '5000'))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    if origin.strip()
]

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
NOTIFICATIONS_ENABLED = _env_bool('NOTIFICATIONS_ENABLED', default=False)

AUTH_TOKEN_MAX_AGE_SECONDS = int(os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', str(60 * 60 * 24)))
