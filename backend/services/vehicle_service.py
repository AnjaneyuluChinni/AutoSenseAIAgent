from database.models import Vehicle, User, get_db_session
from backend.agents.orchestrator import MasterOrchestrator
from datetime import datetime

orchestrator = MasterOrchestrator()

def get_user_vehicles(user_id: int) -> list:
    db = get_db_session()
    try:
        vehicles = db.query(Vehicle).filter(Vehicle.owner_id == user_id).all()
        result = []
        for v in vehicles:
            result.append({
                'id': v.id,
                'registration_number': v.registration_number,
                'make': v.make,
                'model': v.model,
                'year': v.year,
                'engine_health': v.engine_health,
                'brake_health': v.brake_health,
                'battery_health': v.battery_health,
                'tire_health': v.tire_health,
                'last_service_date': v.last_service_date.isoformat() if v.last_service_date else None,
                'next_service_date': v.next_service_date.isoformat() if v.next_service_date else None,
                'total_km': v.total_km,
                'avg_km_per_month': v.avg_km_per_month
            })
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_vehicle_details(vehicle_id: int) -> dict:
    db = get_db_session()
    try:
        v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not v:
            db.close()
            return None
        
        result = {
            'id': v.id,
            'owner_id': v.owner_id,
            'registration_number': v.registration_number,
            'make': v.make,
            'model': v.model,
            'year': v.year,
            'vin': v.vin,
            'engine_health': v.engine_health,
            'brake_health': v.brake_health,
            'battery_health': v.battery_health,
            'tire_health': v.tire_health,
            'last_service_date': v.last_service_date.isoformat() if v.last_service_date else None,
            'next_service_date': v.next_service_date.isoformat() if v.next_service_date else None,
            'total_km': v.total_km,
            'avg_km_per_month': v.avg_km_per_month,
            'service_interval_km': v.service_interval_km,
            'service_interval_months': v.service_interval_months,
            'latitude': v.latitude,
            'longitude': v.longitude
        }
        db.close()
        return result
    except Exception as e:
        db.close()
        return None

def get_vehicle_prediction(vehicle_id: int, user_id: int = None) -> dict:
    vehicle = get_vehicle_details(vehicle_id)
    if not vehicle:
        return {"success": False, "error": "Vehicle not found"}
    
    db = get_db_session()
    from database.models import BreakdownEvent
    breakdown_count = db.query(BreakdownEvent).filter(
        BreakdownEvent.vehicle_id == vehicle_id
    ).count()
    db.close()
    
    prediction_input = {
        'task_type': 'predict_service',
        'user_id': user_id,
        'vehicle_id': vehicle_id,
        'last_service_date': vehicle.get('last_service_date'),
        'avg_km_per_month': vehicle.get('avg_km_per_month', 1000),
        'service_interval_km': vehicle.get('service_interval_km', 10000),
        'service_interval_months': vehicle.get('service_interval_months', 6),
        'breakdown_count': breakdown_count,
        'engine_health': vehicle.get('engine_health', 100),
        'brake_health': vehicle.get('brake_health', 100),
        'battery_health': vehicle.get('battery_health', 100)
    }
    
    return orchestrator.run(prediction_input)

def get_all_vehicles() -> list:
    db = get_db_session()
    try:
        vehicles = db.query(Vehicle).all()
        result = []
        for v in vehicles:
            owner = db.query(User).filter(User.id == v.owner_id).first()
            result.append({
                'id': v.id,
                'owner_name': owner.full_name if owner else 'Unknown',
                'owner_id': v.owner_id,
                'registration_number': v.registration_number,
                'make': v.make,
                'model': v.model,
                'year': v.year,
                'engine_health': v.engine_health,
                'brake_health': v.brake_health,
                'battery_health': v.battery_health,
                'last_service_date': v.last_service_date.isoformat() if v.last_service_date else None,
                'total_km': v.total_km
            })
        db.close()
        return result
    except Exception as e:
        db.close()
        return []
