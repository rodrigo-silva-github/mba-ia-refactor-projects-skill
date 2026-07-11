"""Orquestração dos casos de uso de User: validação, autenticação e serialização."""
import logging

from database import db
from middlewares.auth import generate_token
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, validate_email

logger = logging.getLogger(__name__)


def _task_summary_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'overdue': task.is_overdue(),
    }


def list_users():
    users = User.query.all()
    return [
        {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': len(u.tasks),
        }
        for u in users
    ]


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    tasks = Task.query.filter_by(user_id=user_id).all()
    return [_task_summary_dict(t) for t in tasks]


def create_user(data):
    if not data:
        return None, 'Dados inválidos', 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return None, 'Nome é obrigatório', 400
    if not email:
        return None, 'Email é obrigatório', 400
    if not password:
        return None, 'Senha é obrigatória', 400
    if not validate_email(email):
        return None, 'Email inválido', 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return None, 'Senha deve ter no mínimo 4 caracteres', 400

    if User.query.filter_by(email=email).first():
        return None, 'Email já cadastrado', 409

    if role not in VALID_ROLES:
        return None, 'Role inválido', 400

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_criar_usuario')
        return None, 'Erro ao criar usuário', 500

    logger.info('usuario_criado', extra={'user_id': user.id})
    return user.to_dict(), None, 201


def update_user(user_id, data, acting_user):
    user = User.query.get(user_id)
    if not user:
        return None, 'Usuário não encontrado', 404

    if not data:
        return None, 'Dados inválidos', 400

    is_self = acting_user.id == user.id
    if not is_self and not acting_user.is_admin():
        return None, 'Você só pode alterar o seu próprio usuário', 403

    if ('role' in data or 'active' in data) and not acting_user.is_admin():
        return None, 'Apenas administradores podem alterar role/active', 403

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            return None, 'Email inválido', 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return None, 'Email já cadastrado', 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return None, 'Senha muito curta', 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return None, 'Role inválido', 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_atualizar_usuario')
        return None, 'Erro ao atualizar', 500

    return user.to_dict(), None, 200


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, 'Usuário não encontrado', 404

    try:
        Task.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('erro_deletar_usuario')
        return False, 'Erro ao deletar', 500

    logger.info('usuario_deletado', extra={'user_id': user_id})
    return True, None, 200


def login(data):
    if not data:
        return None, 'Dados inválidos', 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return None, 'Email e senha são obrigatórios', 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None, 'Credenciais inválidas', 401

    if not user.active:
        return None, 'Usuário inativo', 403

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user.id),
    }, None, 200
