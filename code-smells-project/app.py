import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database.connection import close_db, init_db
from middlewares.error_handler import registrar_error_handlers
from views.admin_routes import bp as admin_bp
from views.health_routes import bp as health_bp
from views.main_routes import bp as main_bp
from views.pedido_routes import bp as pedidos_bp
from views.produto_routes import bp as produtos_bp
from views.relatorio_routes import bp as relatorios_bp
from views.usuario_routes import bp as usuarios_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
CORS(app)

app.teardown_appcontext(close_db)
registrar_error_handlers(app)

app.register_blueprint(main_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(health_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    init_db()
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://localhost:5000")
    logger.info("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
