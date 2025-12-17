from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
import os

from utils.auth import create_access_token, decode_token, hash_password, verify_password
from database.models import User, get_db_session, init_db
from backend.services.vehicle_service import get_user_vehicles, get_vehicle_details, get_vehicle_prediction, get_all_vehicles
from backend.services.service_request_service import schedule_service, get_user_service_requests, get_all_service_requests, update_service_status
from backend.services.breakdown_service import report_breakdown, get_user_breakdowns, get_all_breakdowns, update_breakdown_status, get_breakdown_details
from backend.services.garage_service import get_all_garages, get_garage_details, add_garage, update_garage, delete_garage, get_nearby_garages
from backend.services.spare_parts_service import get_all_spare_parts, get_parts_for_breakdown, add_spare_part, update_spare_part
from backend.services.analytics_service import get_dashboard_stats, get_breakdown_analytics, get_service_analytics, get_garage_performance, get_agent_logs
from backend.services.alert_service import get_user_alerts, mark_alert_read, dismiss_alert, get_all_alerts
from backend.agents.orchestrator import MasterOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'autosense-secret-2024')
CORS(app)

orchestrator = MasterOrchestrator()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Token is invalid or expired'}), 401
        
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'user') or request.user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    db = get_db_session()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    token = create_access_token({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    })
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role
        }
    })

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token():
    return jsonify({'success': True, 'user': request.user})


@app.route('/api/vehicles', methods=['GET'])
@token_required
def get_vehicles():
    user_id = request.user.get('user_id')
    if request.user.get('role') == 'admin':
        vehicles = get_all_vehicles()
    else:
        vehicles = get_user_vehicles(user_id)
    return jsonify({'success': True, 'vehicles': vehicles})

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET'])
@token_required
def get_vehicle(vehicle_id):
    vehicle = get_vehicle_details(vehicle_id)
    if not vehicle:
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    return jsonify({'success': True, 'vehicle': vehicle})

@app.route('/api/vehicles/<int:vehicle_id>/prediction', methods=['GET'])
@token_required
def get_prediction(vehicle_id):
    user_id = request.user.get('user_id')
    result = get_vehicle_prediction(vehicle_id, user_id)
    return jsonify(result)


@app.route('/api/services', methods=['GET'])
@token_required
def get_services():
    user_id = request.user.get('user_id')
    if request.user.get('role') == 'admin':
        services = get_all_service_requests()
    else:
        services = get_user_service_requests(user_id)
    return jsonify({'success': True, 'services': services})

@app.route('/api/services', methods=['POST'])
@token_required
def create_service():
    data = request.get_json()
    result = schedule_service(
        vehicle_id=data.get('vehicle_id'),
        preferred_date=data.get('preferred_date'),
        garage_id=data.get('garage_id'),
        service_type=data.get('service_type', 'Regular Service')
    )
    return jsonify(result)

@app.route('/api/services/<int:service_id>', methods=['PATCH'])
@token_required
@admin_required
def update_service(service_id):
    data = request.get_json()
    result = update_service_status(
        service_id,
        data.get('status'),
        data.get('garage_id'),
        data.get('actual_cost')
    )
    return jsonify(result)


@app.route('/api/breakdowns', methods=['GET'])
@token_required
def get_breakdowns():
    user_id = request.user.get('user_id')
    if request.user.get('role') == 'admin':
        breakdowns = get_all_breakdowns()
    else:
        breakdowns = get_user_breakdowns(user_id)
    return jsonify({'success': True, 'breakdowns': breakdowns})

@app.route('/api/breakdowns', methods=['POST'])
@token_required
def create_breakdown():
    data = request.get_json()
    result = report_breakdown(
        vehicle_id=data.get('vehicle_id'),
        breakdown_type=data.get('breakdown_type'),
        description=data.get('description', ''),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    return jsonify(result)

@app.route('/api/breakdowns/<int:breakdown_id>', methods=['GET'])
@token_required
def get_breakdown(breakdown_id):
    breakdown = get_breakdown_details(breakdown_id)
    if not breakdown:
        return jsonify({'success': False, 'error': 'Breakdown not found'}), 404
    return jsonify({'success': True, 'breakdown': breakdown})

@app.route('/api/breakdowns/<int:breakdown_id>', methods=['PATCH'])
@token_required
@admin_required
def update_breakdown(breakdown_id):
    data = request.get_json()
    result = update_breakdown_status(
        breakdown_id,
        data.get('status'),
        data.get('garage_id'),
        data.get('actual_cost')
    )
    return jsonify(result)


@app.route('/api/garages', methods=['GET'])
def list_garages():
    garages = get_all_garages()
    return jsonify({'success': True, 'garages': garages})

@app.route('/api/garages/<int:garage_id>', methods=['GET'])
def get_garage_info(garage_id):
    garage = get_garage_details(garage_id)
    if not garage:
        return jsonify({'success': False, 'error': 'Garage not found'}), 404
    return jsonify({'success': True, 'garage': garage})

@app.route('/api/garages/nearby', methods=['GET'])
def find_nearby_garages():
    lat = request.args.get('latitude', type=float)
    lng = request.args.get('longitude', type=float)
    breakdown_type = request.args.get('breakdown_type')
    limit = request.args.get('limit', 5, type=int)
    
    result = get_nearby_garages(lat, lng, breakdown_type, limit)
    return jsonify(result)

@app.route('/api/garages', methods=['POST'])
@token_required
@admin_required
def create_garage():
    data = request.get_json()
    result = add_garage(
        name=data.get('name'),
        address=data.get('address'),
        city=data.get('city'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        phone=data.get('phone'),
        email=data.get('email'),
        capacity=data.get('capacity', 10),
        opening_time=data.get('opening_time', '08:00'),
        closing_time=data.get('closing_time', '18:00'),
        working_days=data.get('working_days', 'Mon-Sat'),
        supported_services=data.get('supported_services')
    )
    return jsonify(result)

@app.route('/api/garages/<int:garage_id>', methods=['PATCH'])
@token_required
@admin_required
def patch_garage(garage_id):
    data = request.get_json()
    result = update_garage(garage_id, **data)
    return jsonify(result)

@app.route('/api/garages/<int:garage_id>', methods=['DELETE'])
@token_required
@admin_required
def remove_garage(garage_id):
    result = delete_garage(garage_id)
    return jsonify(result)


@app.route('/api/parts', methods=['GET'])
def list_parts():
    parts = get_all_spare_parts()
    return jsonify({'success': True, 'parts': parts})

@app.route('/api/parts/for-breakdown', methods=['GET'])
def parts_for_breakdown():
    breakdown_type = request.args.get('breakdown_type')
    vehicle_make = request.args.get('vehicle_make')
    vehicle_model = request.args.get('vehicle_model')
    
    result = get_parts_for_breakdown(breakdown_type, vehicle_make, vehicle_model)
    return jsonify(result)

@app.route('/api/parts', methods=['POST'])
@token_required
@admin_required
def create_part():
    data = request.get_json()
    result = add_spare_part(
        part_number=data.get('part_number'),
        name=data.get('name'),
        category=data.get('category'),
        oem_price=data.get('oem_price'),
        aftermarket_price=data.get('aftermarket_price'),
        quantity=data.get('quantity', 0),
        minimum_stock=data.get('minimum_stock', 5),
        compatible_makes=data.get('compatible_makes'),
        breakdown_types=data.get('breakdown_types')
    )
    return jsonify(result)

@app.route('/api/parts/<int:part_id>', methods=['PATCH'])
@token_required
@admin_required
def patch_part(part_id):
    data = request.get_json()
    result = update_spare_part(part_id, **data)
    return jsonify(result)


@app.route('/api/alerts', methods=['GET'])
@token_required
def get_alerts_list():
    user_id = request.user.get('user_id')
    include_read = request.args.get('include_read', 'false').lower() == 'true'
    
    if request.user.get('role') == 'admin':
        alerts = get_all_alerts()
    else:
        alerts = get_user_alerts(user_id, include_read)
    
    return jsonify({'success': True, 'alerts': alerts})

@app.route('/api/alerts/<int:alert_id>/read', methods=['POST'])
@token_required
def mark_read(alert_id):
    result = mark_alert_read(alert_id)
    return jsonify(result)

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@token_required
def dismiss(alert_id):
    result = dismiss_alert(alert_id)
    return jsonify(result)


@app.route('/api/analytics/dashboard', methods=['GET'])
@token_required
@admin_required
def dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/analytics/breakdowns', methods=['GET'])
@token_required
@admin_required
def breakdown_analytics():
    analytics = get_breakdown_analytics()
    return jsonify({'success': True, 'analytics': analytics})

@app.route('/api/analytics/services', methods=['GET'])
@token_required
@admin_required
def service_analytics():
    analytics = get_service_analytics()
    return jsonify({'success': True, 'analytics': analytics})

@app.route('/api/analytics/garages', methods=['GET'])
@token_required
@admin_required
def garage_analytics():
    performance = get_garage_performance()
    return jsonify({'success': True, 'performance': performance})

@app.route('/api/analytics/agent-logs', methods=['GET'])
@token_required
@admin_required
def agent_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = get_agent_logs(limit)
    return jsonify({'success': True, 'logs': logs})


@app.route('/api/orchestrator/predict', methods=['POST'])
@token_required
def orchestrator_predict():
    data = request.get_json()
    data['task_type'] = 'predict_service'
    result = orchestrator.run(data)
    return jsonify(result)

@app.route('/api/orchestrator/breakdown', methods=['POST'])
@token_required
def orchestrator_breakdown():
    data = request.get_json()
    data['task_type'] = 'breakdown_emergency'
    result = orchestrator.run(data)
    return jsonify(result)

@app.route('/api/orchestrator/schedule', methods=['POST'])
@token_required
def orchestrator_schedule():
    data = request.get_json()
    data['task_type'] = 'schedule_service'
    result = orchestrator.run(data)
    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'AutoSenseAI API'})

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'service': 'AutoSenseAI API',
        'version': '1.0.0',
        'endpoints': {
            'auth': ['/api/auth/login', '/api/auth/verify'],
            'vehicles': ['/api/vehicles', '/api/vehicles/<id>', '/api/vehicles/<id>/prediction'],
            'services': ['/api/services'],
            'breakdowns': ['/api/breakdowns'],
            'garages': ['/api/garages', '/api/garages/nearby'],
            'parts': ['/api/parts'],
            'alerts': ['/api/alerts'],
            'analytics': ['/api/analytics/dashboard', '/api/analytics/breakdowns', '/api/analytics/services'],
            'orchestrator': ['/api/orchestrator/predict', '/api/orchestrator/breakdown', '/api/orchestrator/schedule']
        }
    })


def create_app():
    init_db()
    return app

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
