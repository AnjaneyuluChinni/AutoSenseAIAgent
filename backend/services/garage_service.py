from database.models import Garage, ServiceSlot, get_db_session
from backend.agents.orchestrator import MasterOrchestrator
from datetime import datetime, timedelta

orchestrator = MasterOrchestrator()

def get_all_garages() -> list:
    db = get_db_session()
    try:
        garages = db.query(Garage).filter(Garage.is_active == True).all()
        
        result = []
        for g in garages:
            result.append({
                'id': g.id,
                'name': g.name,
                'address': g.address,
                'city': g.city,
                'latitude': g.latitude,
                'longitude': g.longitude,
                'phone': g.phone,
                'email': g.email,
                'capacity': g.capacity,
                'current_load': g.current_load,
                'available_capacity': g.capacity - g.current_load,
                'opening_time': g.opening_time,
                'closing_time': g.closing_time,
                'working_days': g.working_days,
                'supported_services': g.supported_services,
                'rating': g.rating,
                'avg_repair_time_hours': g.avg_repair_time_hours,
                'is_active': g.is_active
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_garage_details(garage_id: int) -> dict:
    db = get_db_session()
    try:
        g = db.query(Garage).filter(Garage.id == garage_id).first()
        if not g:
            db.close()
            return None
        
        result = {
            'id': g.id,
            'name': g.name,
            'address': g.address,
            'city': g.city,
            'latitude': g.latitude,
            'longitude': g.longitude,
            'phone': g.phone,
            'email': g.email,
            'capacity': g.capacity,
            'current_load': g.current_load,
            'available_capacity': g.capacity - g.current_load,
            'opening_time': g.opening_time,
            'closing_time': g.closing_time,
            'working_days': g.working_days,
            'supported_services': g.supported_services,
            'rating': g.rating,
            'avg_repair_time_hours': g.avg_repair_time_hours,
            'is_active': g.is_active
        }
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return None

def add_garage(name: str, address: str, city: str, latitude: float, longitude: float,
               phone: str = None, email: str = None, capacity: int = 10,
               opening_time: str = "08:00", closing_time: str = "18:00",
               working_days: str = "Mon-Sat", supported_services: str = None) -> dict:
    db = get_db_session()
    try:
        garage = Garage(
            name=name,
            address=address,
            city=city,
            latitude=latitude,
            longitude=longitude,
            phone=phone,
            email=email,
            capacity=capacity,
            opening_time=opening_time,
            closing_time=closing_time,
            working_days=working_days,
            supported_services=supported_services,
            is_active=True
        )
        
        db.add(garage)
        db.commit()
        
        for i in range(14):
            date = datetime.now() + timedelta(days=i)
            for slot_time in ["09:00-12:00", "12:00-15:00", "15:00-18:00"]:
                slot = ServiceSlot(
                    garage_id=garage.id,
                    date=date,
                    time_slot=slot_time,
                    is_available=True,
                    max_capacity=3,
                    current_bookings=0
                )
                db.add(slot)
        
        db.commit()
        garage_id = garage.id
        db.close()
        
        return {"success": True, "garage_id": garage_id}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def update_garage(garage_id: int, **kwargs) -> dict:
    db = get_db_session()
    try:
        garage = db.query(Garage).filter(Garage.id == garage_id).first()
        if not garage:
            db.close()
            return {"success": False, "error": "Garage not found"}
        
        for key, value in kwargs.items():
            if hasattr(garage, key) and value is not None:
                setattr(garage, key, value)
        
        db.commit()
        db.close()
        
        return {"success": True, "message": "Garage updated successfully"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def delete_garage(garage_id: int) -> dict:
    db = get_db_session()
    try:
        garage = db.query(Garage).filter(Garage.id == garage_id).first()
        if not garage:
            db.close()
            return {"success": False, "error": "Garage not found"}
        
        garage.is_active = False
        db.commit()
        db.close()
        
        return {"success": True, "message": "Garage deactivated successfully"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def get_nearby_garages(latitude: float, longitude: float, 
                       breakdown_type: str = None, limit: int = 5) -> dict:
    recommendation_agent = orchestrator.get_agent('garage_recommendation')
    
    input_data = {
        'latitude': latitude,
        'longitude': longitude,
        'breakdown_type': breakdown_type,
        'limit': limit
    }
    
    return recommendation_agent.run(input_data)
