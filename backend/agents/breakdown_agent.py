from backend.agents.base_agent import BaseAgent
from datetime import datetime
from database.models import BreakdownEvent, Vehicle, get_db_session

class BreakdownAgent(BaseAgent):
    def __init__(self):
        super().__init__("BreakdownAgent")
    
    def execute(self, input_data: dict) -> dict:
        vehicle_id = input_data.get('vehicle_id')
        breakdown_type = input_data.get('breakdown_type', 'Unknown')
        description = input_data.get('description', '')
        latitude = input_data.get('latitude')
        longitude = input_data.get('longitude')
        
        db = get_db_session()
        
        try:
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            
            if not vehicle:
                db.close()
                return {"success": False, "error": "Vehicle not found"}
            
            if latitude is None:
                latitude = vehicle.latitude or 28.6139
            if longitude is None:
                longitude = vehicle.longitude or 77.2090
            
            breakdown_event = BreakdownEvent(
                vehicle_id=vehicle_id,
                breakdown_type=breakdown_type,
                description=description,
                vehicle_latitude=latitude,
                vehicle_longitude=longitude,
                status='reported',
                reported_at=datetime.now()
            )
            
            db.add(breakdown_event)
            db.commit()
            
            event_id = breakdown_event.id
            
            result = {
                "success": True,
                "breakdown_event_id": event_id,
                "status": "reported",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "breakdown_type": breakdown_type,
                "next_steps": [
                    "Finding nearby garages",
                    "Calculating ETAs",
                    "Preparing cost estimates"
                ],
                "decision": f"Created breakdown event #{event_id} for {breakdown_type}"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "error": str(e)}
    
    def assign_garage(self, breakdown_id: int, garage_id: int) -> dict:
        db = get_db_session()
        
        try:
            breakdown = db.query(BreakdownEvent).filter(
                BreakdownEvent.id == breakdown_id
            ).first()
            
            if not breakdown:
                db.close()
                return {"success": False, "error": "Breakdown event not found"}
            
            breakdown.garage_id = garage_id
            breakdown.status = 'garage_assigned'
            breakdown.garage_assigned_at = datetime.now()
            
            db.commit()
            db.close()
            
            return {
                "success": True,
                "breakdown_id": breakdown_id,
                "garage_id": garage_id,
                "status": "garage_assigned",
                "decision": f"Assigned garage #{garage_id} to breakdown #{breakdown_id}"
            }
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "error": str(e)}
    
    def update_status(self, breakdown_id: int, new_status: str) -> dict:
        db = get_db_session()
        
        try:
            breakdown = db.query(BreakdownEvent).filter(
                BreakdownEvent.id == breakdown_id
            ).first()
            
            if not breakdown:
                db.close()
                return {"success": False, "error": "Breakdown event not found"}
            
            breakdown.status = new_status
            
            if new_status == 'garage_en_route':
                pass
            elif new_status == 'repair_in_progress':
                breakdown.repair_started_at = datetime.now()
            elif new_status == 'completed':
                breakdown.completed_at = datetime.now()
                if breakdown.repair_started_at:
                    repair_minutes = (datetime.now() - breakdown.repair_started_at).total_seconds() / 60
                    breakdown.actual_repair_minutes = int(repair_minutes)
            
            db.commit()
            db.close()
            
            return {
                "success": True,
                "breakdown_id": breakdown_id,
                "new_status": new_status,
                "decision": f"Updated breakdown #{breakdown_id} status to {new_status}"
            }
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "error": str(e)}
