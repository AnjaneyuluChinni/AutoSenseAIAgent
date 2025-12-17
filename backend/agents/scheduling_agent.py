from backend.agents.base_agent import BaseAgent
from datetime import datetime, timedelta
from database.models import ServiceSlot, ServiceRequest, Garage, get_db_session

class SchedulingAgent(BaseAgent):
    def __init__(self):
        super().__init__("SchedulingAgent")
    
    def execute(self, input_data: dict) -> dict:
        vehicle_id = input_data.get('vehicle_id')
        preferred_date = input_data.get('preferred_date')
        garage_id = input_data.get('garage_id')
        service_type = input_data.get('service_type', 'Regular Service')
        
        if isinstance(preferred_date, str):
            preferred_date = datetime.fromisoformat(preferred_date)
        
        db = get_db_session()
        
        try:
            available_slot = None
            selected_garage = None
            
            if garage_id:
                slot = db.query(ServiceSlot).filter(
                    ServiceSlot.garage_id == garage_id,
                    ServiceSlot.date >= preferred_date,
                    ServiceSlot.is_available == True,
                    ServiceSlot.current_bookings < ServiceSlot.max_capacity
                ).order_by(ServiceSlot.date).first()
                
                if slot:
                    available_slot = slot
                    selected_garage = db.query(Garage).filter(Garage.id == garage_id).first()
            
            if not available_slot:
                slots = db.query(ServiceSlot).join(Garage).filter(
                    ServiceSlot.date >= preferred_date,
                    ServiceSlot.is_available == True,
                    ServiceSlot.current_bookings < ServiceSlot.max_capacity,
                    Garage.is_active == True
                ).order_by(ServiceSlot.date).limit(5).all()
                
                if slots:
                    available_slot = slots[0]
                    selected_garage = db.query(Garage).filter(
                        Garage.id == available_slot.garage_id
                    ).first()
            
            if not available_slot:
                search_date = preferred_date
                for i in range(14):
                    search_date = preferred_date + timedelta(days=i)
                    garages = db.query(Garage).filter(Garage.is_active == True).all()
                    
                    for garage in garages:
                        if garage.current_load < garage.capacity:
                            new_slot = ServiceSlot(
                                garage_id=garage.id,
                                date=search_date,
                                time_slot="09:00-12:00",
                                is_available=True,
                                max_capacity=3,
                                current_bookings=0
                            )
                            db.add(new_slot)
                            db.commit()
                            available_slot = new_slot
                            selected_garage = garage
                            break
                    
                    if available_slot:
                        break
            
            if available_slot and selected_garage:
                service_request = ServiceRequest(
                    vehicle_id=vehicle_id,
                    garage_id=selected_garage.id,
                    service_type=service_type,
                    requested_date=preferred_date,
                    scheduled_date=available_slot.date,
                    status='open',
                    priority='medium'
                )
                db.add(service_request)
                
                available_slot.current_bookings += 1
                if available_slot.current_bookings >= available_slot.max_capacity:
                    available_slot.is_available = False
                
                db.commit()
                
                result = {
                    "success": True,
                    "slot_found": True,
                    "scheduled_date": available_slot.date.isoformat(),
                    "time_slot": available_slot.time_slot,
                    "garage_name": selected_garage.name,
                    "garage_id": selected_garage.id,
                    "service_request_id": service_request.id,
                    "is_preferred_date": available_slot.date.date() == preferred_date.date(),
                    "decision": f"Scheduled service at {selected_garage.name} on {available_slot.date.strftime('%Y-%m-%d')}"
                }
            else:
                result = {
                    "success": True,
                    "slot_found": False,
                    "message": "No available slots found in the next 14 days",
                    "decision": "Unable to find available slot"
                }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "error": str(e)}
