from database.models import ServiceRequest, Vehicle, Garage, get_db_session
from backend.agents.orchestrator import MasterOrchestrator
from datetime import datetime

orchestrator = MasterOrchestrator()

def schedule_service(vehicle_id: int, preferred_date: datetime, 
                     garage_id: int = None, service_type: str = "Regular Service") -> dict:
    scheduling_input = {
        'task_type': 'schedule_service',
        'vehicle_id': vehicle_id,
        'preferred_date': preferred_date.isoformat() if isinstance(preferred_date, datetime) else preferred_date,
        'garage_id': garage_id,
        'service_type': service_type
    }
    
    return orchestrator.run(scheduling_input)

def get_user_service_requests(user_id: int) -> list:
    db = get_db_session()
    try:
        vehicles = db.query(Vehicle).filter(Vehicle.owner_id == user_id).all()
        vehicle_ids = [v.id for v in vehicles]
        
        requests = db.query(ServiceRequest).filter(
            ServiceRequest.vehicle_id.in_(vehicle_ids)
        ).order_by(ServiceRequest.created_at.desc()).all()
        
        result = []
        for r in requests:
            vehicle = db.query(Vehicle).filter(Vehicle.id == r.vehicle_id).first()
            garage = db.query(Garage).filter(Garage.id == r.garage_id).first() if r.garage_id else None
            
            result.append({
                'id': r.id,
                'vehicle_id': r.vehicle_id,
                'vehicle_name': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
                'registration_number': vehicle.registration_number if vehicle else '',
                'garage_name': garage.name if garage else 'Not assigned',
                'service_type': r.service_type,
                'status': r.status,
                'priority': r.priority,
                'requested_date': r.requested_date.isoformat() if r.requested_date else None,
                'scheduled_date': r.scheduled_date.isoformat() if r.scheduled_date else None,
                'completed_date': r.completed_date.isoformat() if r.completed_date else None,
                'estimated_cost': r.estimated_cost,
                'actual_cost': r.actual_cost
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_all_service_requests() -> list:
    db = get_db_session()
    try:
        requests = db.query(ServiceRequest).order_by(ServiceRequest.created_at.desc()).all()
        
        result = []
        for r in requests:
            vehicle = db.query(Vehicle).filter(Vehicle.id == r.vehicle_id).first()
            garage = db.query(Garage).filter(Garage.id == r.garage_id).first() if r.garage_id else None
            
            result.append({
                'id': r.id,
                'vehicle_id': r.vehicle_id,
                'vehicle_name': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
                'registration_number': vehicle.registration_number if vehicle else '',
                'garage_id': r.garage_id,
                'garage_name': garage.name if garage else 'Not assigned',
                'service_type': r.service_type,
                'status': r.status,
                'priority': r.priority,
                'requested_date': r.requested_date.isoformat() if r.requested_date else None,
                'scheduled_date': r.scheduled_date.isoformat() if r.scheduled_date else None,
                'completed_date': r.completed_date.isoformat() if r.completed_date else None,
                'estimated_cost': r.estimated_cost,
                'actual_cost': r.actual_cost,
                'created_at': r.created_at.isoformat() if r.created_at else None
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def update_service_status(request_id: int, new_status: str, 
                          garage_id: int = None, actual_cost: float = None) -> dict:
    db = get_db_session()
    try:
        request = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
        
        if not request:
            db.close()
            return {"success": False, "error": "Service request not found"}
        
        request.status = new_status
        
        if garage_id:
            request.garage_id = garage_id
        
        if actual_cost:
            request.actual_cost = actual_cost
        
        if new_status == 'completed':
            request.completed_date = datetime.now()
        
        db.commit()
        db.close()
        
        return {"success": True, "message": f"Status updated to {new_status}"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}
