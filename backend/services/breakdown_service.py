from database.models import BreakdownEvent, Vehicle, Garage, get_db_session
from backend.agents.orchestrator import MasterOrchestrator
from datetime import datetime

orchestrator = MasterOrchestrator()

def report_breakdown(vehicle_id: int, breakdown_type: str, description: str = "",
                    latitude: float = None, longitude: float = None) -> dict:
    db = get_db_session()
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    vehicle_make = vehicle.make if vehicle else ''
    vehicle_model = vehicle.model if vehicle else ''
    db.close()
    
    breakdown_input = {
        'task_type': 'breakdown_emergency',
        'vehicle_id': vehicle_id,
        'breakdown_type': breakdown_type,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'vehicle_make': vehicle_make,
        'vehicle_model': vehicle_model
    }
    
    return orchestrator.run(breakdown_input)

def get_user_breakdowns(user_id: int) -> list:
    db = get_db_session()
    try:
        vehicles = db.query(Vehicle).filter(Vehicle.owner_id == user_id).all()
        vehicle_ids = [v.id for v in vehicles]
        
        breakdowns = db.query(BreakdownEvent).filter(
            BreakdownEvent.vehicle_id.in_(vehicle_ids)
        ).order_by(BreakdownEvent.reported_at.desc()).all()
        
        result = []
        for b in breakdowns:
            vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()
            garage = db.query(Garage).filter(Garage.id == b.garage_id).first() if b.garage_id else None
            
            result.append({
                'id': b.id,
                'vehicle_id': b.vehicle_id,
                'vehicle_name': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
                'breakdown_type': b.breakdown_type,
                'description': b.description,
                'status': b.status,
                'garage_name': garage.name if garage else 'Not assigned',
                'reported_at': b.reported_at.isoformat() if b.reported_at else None,
                'completed_at': b.completed_at.isoformat() if b.completed_at else None,
                'estimated_cost': b.estimated_cost,
                'actual_cost': b.actual_cost,
                'estimated_arrival_minutes': b.estimated_arrival_minutes,
                'estimated_repair_minutes': b.estimated_repair_minutes
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_all_breakdowns() -> list:
    db = get_db_session()
    try:
        breakdowns = db.query(BreakdownEvent).order_by(BreakdownEvent.reported_at.desc()).all()
        
        result = []
        for b in breakdowns:
            vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()
            garage = db.query(Garage).filter(Garage.id == b.garage_id).first() if b.garage_id else None
            
            result.append({
                'id': b.id,
                'vehicle_id': b.vehicle_id,
                'vehicle_name': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
                'registration_number': vehicle.registration_number if vehicle else '',
                'breakdown_type': b.breakdown_type,
                'description': b.description,
                'status': b.status,
                'garage_id': b.garage_id,
                'garage_name': garage.name if garage else 'Not assigned',
                'vehicle_latitude': b.vehicle_latitude,
                'vehicle_longitude': b.vehicle_longitude,
                'reported_at': b.reported_at.isoformat() if b.reported_at else None,
                'garage_assigned_at': b.garage_assigned_at.isoformat() if b.garage_assigned_at else None,
                'completed_at': b.completed_at.isoformat() if b.completed_at else None,
                'estimated_cost': b.estimated_cost,
                'actual_cost': b.actual_cost
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def update_breakdown_status(breakdown_id: int, new_status: str, 
                           garage_id: int = None, actual_cost: float = None) -> dict:
    breakdown_agent = orchestrator.get_agent('breakdown')
    
    if garage_id and new_status == 'garage_assigned':
        result = breakdown_agent.assign_garage(breakdown_id, garage_id)
        if not result.get('success'):
            return result
    
    result = breakdown_agent.update_status(breakdown_id, new_status)
    
    if actual_cost and result.get('success'):
        db = get_db_session()
        breakdown = db.query(BreakdownEvent).filter(BreakdownEvent.id == breakdown_id).first()
        if breakdown:
            breakdown.actual_cost = actual_cost
            db.commit()
        db.close()
    
    return result

def get_breakdown_details(breakdown_id: int) -> dict:
    db = get_db_session()
    try:
        b = db.query(BreakdownEvent).filter(BreakdownEvent.id == breakdown_id).first()
        if not b:
            db.close()
            return None
        
        vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()
        garage = db.query(Garage).filter(Garage.id == b.garage_id).first() if b.garage_id else None
        
        result = {
            'id': b.id,
            'vehicle_id': b.vehicle_id,
            'vehicle_name': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
            'registration_number': vehicle.registration_number if vehicle else '',
            'breakdown_type': b.breakdown_type,
            'description': b.description,
            'status': b.status,
            'garage_id': b.garage_id,
            'garage_name': garage.name if garage else 'Not assigned',
            'garage_address': garage.address if garage else '',
            'garage_phone': garage.phone if garage else '',
            'vehicle_latitude': b.vehicle_latitude,
            'vehicle_longitude': b.vehicle_longitude,
            'garage_current_lat': b.garage_current_lat,
            'garage_current_lng': b.garage_current_lng,
            'reported_at': b.reported_at.isoformat() if b.reported_at else None,
            'garage_assigned_at': b.garage_assigned_at.isoformat() if b.garage_assigned_at else None,
            'garage_arrived_at': b.garage_arrived_at.isoformat() if b.garage_arrived_at else None,
            'repair_started_at': b.repair_started_at.isoformat() if b.repair_started_at else None,
            'completed_at': b.completed_at.isoformat() if b.completed_at else None,
            'estimated_arrival_minutes': b.estimated_arrival_minutes,
            'estimated_repair_minutes': b.estimated_repair_minutes,
            'actual_repair_minutes': b.actual_repair_minutes,
            'estimated_cost': b.estimated_cost,
            'actual_cost': b.actual_cost
        }
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return None
