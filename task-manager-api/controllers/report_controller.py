"""Orquestração de relatórios agregados e CRUD de categorias."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import DEFAULT_COLOR, calculate_percentage

logger = logging.getLogger(__name__)


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for priority, count in db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority):
        if priority in priority_counts:
            priority_counts[priority] = count

    overdue_count = 0
    overdue_list = []
    for task in Task.query.all():
        if task.is_overdue():
            overdue_count += 1
            overdue_list.append({
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (datetime.utcnow() - task.due_date).days,
            })

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago,
    ).count()

    total_by_user = dict(db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all())
    done_by_user = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )

    user_stats = []
    for u in User.query.all():
        total = total_by_user.get(u.id, 0)
        completed = done_by_user.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(datetime.utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': priority_counts[1],
            'high': priority_counts[2],
            'medium': priority_counts[3],
            'low': priority_counts[4],
            'minimal': priority_counts[5],
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()

    counts_by_status = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in counts_by_status:
            counts_by_status[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': counts_by_status['done'],
            'pending': counts_by_status['pending'],
            'in_progress': counts_by_status['in_progress'],
            'cancelled': counts_by_status['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(counts_by_status['done'], total),
        },
    }


def list_categories():
    task_counts = dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())
    result = []
    for category in Category.query.all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    if not data:
        return None, 'Dados inválidos', 400

    name = data.get('name')
    if not name:
        return None, 'Nome é obrigatório', 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', DEFAULT_COLOR)

    try:
        db.session.add(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_criar_categoria')
        return None, 'Erro ao criar categoria', 500

    return category.to_dict(), None, 201


def update_category(cat_id, data):
    category = Category.query.get(cat_id)
    if not category:
        return None, 'Categoria não encontrada', 404

    if not data:
        return None, 'Dados inválidos', 400

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_atualizar_categoria')
        return None, 'Erro ao atualizar', 500

    return category.to_dict(), None, 200


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return False, 'Categoria não encontrada', 404

    try:
        db.session.delete(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_deletar_categoria')
        return False, 'Erro ao deletar', 500

    return True, None, 200
