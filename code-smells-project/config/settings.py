import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
ADMIN_RESET_KEY = os.environ.get("ADMIN_RESET_KEY", "dev-admin-key-change-me")
