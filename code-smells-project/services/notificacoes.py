import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("notificacao.pedido_criado", extra={"pedido_id": pedido_id, "usuario_id": usuario_id})
    # TODO: integrar provedor real de e-mail/SMS/push (não implementado nesta versão)


def notificar_mudanca_status(pedido_id, novo_status):
    logger.info("notificacao.pedido_status", extra={"pedido_id": pedido_id, "status": novo_status})
    # TODO: integrar provedor real de notificação (não implementado nesta versão)
