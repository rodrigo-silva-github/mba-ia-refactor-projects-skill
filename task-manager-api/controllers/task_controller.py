"""Orquestração dos casos de uso de Task: validação, persistência e serialização."""
import logging

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import notification_service
from utils.helpers import DEFAULT_PRIORITY, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH, calculate_percentage, parse_date

logger = logging.getLogger(__name__)


def _task_detail_dict(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def _validate_task_fields(data, task=None):
    """Valida os campos de uma task. Reaproveitado por create e update (elimina duplicação)."""
    title = data.get('title', task.title if task else None)
    if 'title' in data or task is None:
        if not title:
            return 'Título é obrigatório'
        if len(title) < MIN_TITLE_LENGTH:
            return 'Título muito curto'
        if len(title) > MAX_TITLE_LENGTH:
            return 'Título muito longo'

    if 'status' in data and not Task.validate_status(data['status']):
        return 'Status inválido'

    if 'priority' in data and not Task.validate_priority(data['priority']):
        return 'Prioridade deve ser entre 1 e 5'

    if data.get('user_id'):
        if not User.query.get(data['user_id']):
            return 'Usuário não encontrado', 404

    if data.get('category_id'):
        if not Category.query.get(data['category_id']):
            return 'Categoria não encontrada', 404

    return None


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = _task_detail_dict(task)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None
    return _task_detail_dict(task)


def create_task(data):
    if not data:
        return None, 'Dados inválidos', 400

    error = _validate_task_fields(data)
    if error:
        if isinstance(error, tuple):
            return None, error[0], error[1]
        return None, error, 400

    task = Task()
    task.title = data.get('title')
    task.description = data.get('description', '')
    task.status = data.get('status', 'pending')
    task.priority = data.get('priority', DEFAULT_PRIORITY)
    task.user_id = data.get('user_id')
    task.category_id = data.get('category_id')

    due_date = data.get('due_date')
    if due_date:
        parsed = parse_date(due_date)
        if not parsed:
            return None, 'Formato de data inválido. Use YYYY-MM-DD', 400
        task.due_date = parsed

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    try:
        db.session.add(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_criar_task')
        return None, 'Erro ao criar task', 500

    logger.info('task_criada', extra={'task_id': task.id})
    if task.user_id:
        notification_service.notify_task_assigned(task.user, task)

    return _task_detail_dict(task), None, 201


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404

    if not data:
        return None, 'Dados inválidos', 400

    error = _validate_task_fields(data, task=task)
    if error:
        if isinstance(error, tuple):
            return None, error[0], error[1]
        return None, error, 400

    previous_user_id = task.user_id

    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'user_id' in data:
        task.user_id = data['user_id']
    if 'category_id' in data:
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                return None, 'Formato de data inválido', 400
            task.due_date = parsed
        else:
            task.due_date = None

    if 'tags' in data:
        tags = data['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    from datetime import datetime
    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_atualizar_task')
        return None, 'Erro ao atualizar', 500

    logger.info('task_atualizada', extra={'task_id': task.id})
    if task.user_id and task.user_id != previous_user_id:
        notification_service.notify_task_assigned(task.user, task)

    return _task_detail_dict(task), None, 200


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return False, 'Task não encontrada', 404

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_deletar_task')
        return False, 'Erro ao deletar', 500

    logger.info('task_deletada', extra={'task_id': task_id})
    return True, None, 200


def search_tasks(query, status, priority, user_id):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%'),
            )
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [task.to_dict() for task in tasks.all()]


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for task in Task.query.all() if task.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': calculate_percentage(done, total),
    }
