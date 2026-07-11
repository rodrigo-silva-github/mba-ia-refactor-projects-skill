from flask import Blueprint, g, jsonify, request

from controllers import user_controller
from middlewares.auth import admin_required, login_required

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = user_controller.get_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    tasks = user_controller.get_user_tasks(user_id)
    if tasks is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(tasks), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user, error, status = user_controller.create_user(request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(user), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user, error, status = user_controller.update_user(user_id, request.get_json(silent=True), g.current_user)
    if error:
        return jsonify({'error': error}), status
    return jsonify(user), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    ok, error, status = user_controller.delete_user(user_id)
    if error:
        return jsonify({'error': error}), status
    return jsonify({'message': 'Usuário deletado com sucesso'}), status


@user_bp.route('/login', methods=['POST'])
def login():
    result, error, status = user_controller.login(request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(result), status
