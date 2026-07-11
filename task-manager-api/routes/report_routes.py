from flask import Blueprint, jsonify, request

from controllers import report_controller
from middlewares.auth import admin_required, login_required

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    report = report_controller.user_report(user_id)
    if not report:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(report), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(report_controller.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    category, error, status = report_controller.create_category(request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(category), status


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    category, error, status = report_controller.update_category(cat_id, request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), status
    return jsonify(category), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@admin_required
def delete_category(cat_id):
    ok, error, status = report_controller.delete_category(cat_id)
    if error:
        return jsonify({'error': error}), status
    return jsonify({'message': 'Categoria deletada'}), status
