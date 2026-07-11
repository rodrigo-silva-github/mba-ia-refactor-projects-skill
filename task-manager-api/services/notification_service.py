import logging
import smtplib
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 5


class NotificationService:
    def __init__(self):
        self.notifications = []
        self.email_host = settings.SMTP_HOST
        self.email_port = settings.SMTP_PORT
        self.email_user = settings.SMTP_USER
        self.email_password = settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not settings.NOTIFICATIONS_ENABLED:
            logger.info('notificacao_desabilitada', extra={'to': to, 'subject': subject})
            return False

        try:
            server = smtplib.SMTP(self.email_host, self.email_port, timeout=SMTP_TIMEOUT_SECONDS)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info('email_enviado', extra={'to': to})
            return True
        except Exception:
            logger.exception('erro_enviar_email', extra={'to': to})
            return False

    def notify_task_assigned(self, user, task):
        if not user:
            return
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': datetime.utcnow(),
        })

    def notify_task_overdue(self, user, task):
        if not user:
            return
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]


notification_service = NotificationService()
