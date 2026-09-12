from flask import Blueprint, jsonify
from backend.models.department import Department
from backend.models.document_type import DocumentType
from backend.utils.middleware import login_required

references_bp = Blueprint('references', __name__, url_prefix='/api')


@references_bp.route('/departments', methods=['GET'])
@login_required
def get_departments(current_user):
    try:
        departments = Department.get_all()
        return jsonify({
            'success': True,
            'departments': [dept.to_dict() for dept in departments]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@references_bp.route('/document-types', methods=['GET'])
@login_required
def get_document_types(current_user):
    try:
        types = DocumentType.get_all()
        return jsonify({
            'success': True,
            'types': [doc_type.to_dict() for doc_type in types]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

