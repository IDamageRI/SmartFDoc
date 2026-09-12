from flask import Blueprint, request, jsonify
from backend.utils.middleware import login_required
from backend.services.company_info import CompanyInfoService

company_bp = Blueprint('company', __name__, url_prefix='/api/company')

@company_bp.route('/info', methods=['POST'])
@login_required
def get_company_info(current_user):
    """Получает информацию о компании по ИНН и КПП"""
    try:
        data = request.get_json()
        inn = data.get('inn', '').strip()
        kpp = data.get('kpp', '').strip()
        
        if not inn:
            return jsonify({
                'success': False,
                'error': {'message': 'ИНН не указан'}
            }), 400
        
        if not inn.isdigit() or len(inn) not in [10, 12]:
            return jsonify({
                'success': False,
                'error': {'message': 'ИНН должен содержать 10 или 12 цифр'}
            }), 400
        
        if not kpp:
            return jsonify({
                'success': False,
                'error': {'message': 'КПП не указан'}
            }), 400
        
        if not kpp.isdigit() or len(kpp) != 9:
            return jsonify({
                'success': False,
                'error': {'message': 'КПП должен содержать 9 цифр'}
            }), 400
        
        service = CompanyInfoService()
        company_data = service.get_company_info(inn, kpp)
        
        return jsonify({
            'success': True,
            'data': company_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

