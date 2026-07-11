from flask import Blueprint, jsonify, request

from controllers import task_controller
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result = task_controller.search_tasks(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', ''),
    )
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_controller.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    task, error, status = task_controller.create_task(request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(task), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task, error, status = task_controller.update_task(task_id, request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(task), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    ok, error, status = task_controller.delete_task(task_id)
    if error:
        return jsonify({'error': error}), status
    return jsonify({'message': 'Task deletada com sucesso'}), status
