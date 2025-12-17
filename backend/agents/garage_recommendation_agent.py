from backend.agents.base_agent import BaseAgent
from database.models import Garage, get_db_session
import math

class GarageRecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__("GarageRecommendationAgent")
    
    def execute(self, input_data: dict) -> dict:
        vehicle_lat = input_data.get('latitude')
        vehicle_lng = input_data.get('longitude')
        breakdown_type = input_data.get('breakdown_type', '')
        limit = input_data.get('limit', 5)
        
        if vehicle_lat is None or vehicle_lng is None:
            vehicle_lat = 28.6139
            vehicle_lng = 77.2090
        
        db = get_db_session()
        
        try:
            garages = db.query(Garage).filter(Garage.is_active == True).all()
            
            garage_distances = []
            for garage in garages:
                distance = self.calculate_distance(
                    vehicle_lat, vehicle_lng,
                    garage.latitude, garage.longitude
                )
                
                score = self.calculate_score(garage, distance, breakdown_type)
                
                garage_distances.append({
                    "id": garage.id,
                    "name": garage.name,
                    "address": garage.address,
                    "city": garage.city,
                    "latitude": garage.latitude,
                    "longitude": garage.longitude,
                    "distance_km": distance,
                    "rating": garage.rating,
                    "capacity": garage.capacity,
                    "current_load": garage.current_load,
                    "available_capacity": garage.capacity - garage.current_load,
                    "avg_repair_time_hours": garage.avg_repair_time_hours,
                    "opening_time": garage.opening_time,
                    "closing_time": garage.closing_time,
                    "phone": garage.phone,
                    "score": score
                })
            
            garage_distances.sort(key=lambda x: (-x['score'], x['distance_km']))
            
            recommendations = garage_distances[:limit]
            
            db.close()
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total_garages_found": len(garage_distances),
                "search_location": {
                    "latitude": vehicle_lat,
                    "longitude": vehicle_lng
                },
                "decision": f"Found {len(recommendations)} suitable garages within range"
            }
            
        except Exception as e:
            db.close()
            return {"success": False, "error": str(e)}
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return round(R * c, 2)
    
    def calculate_score(self, garage, distance: float, breakdown_type: str) -> float:
        score = 100
        
        if distance <= 2:
            score += 30
        elif distance <= 5:
            score += 20
        elif distance <= 10:
            score += 10
        else:
            score -= (distance - 10) * 2
        
        score += garage.rating * 5
        
        availability_ratio = (garage.capacity - garage.current_load) / garage.capacity if garage.capacity > 0 else 0
        score += availability_ratio * 20
        
        if garage.avg_repair_time_hours <= 2:
            score += 15
        elif garage.avg_repair_time_hours <= 4:
            score += 10
        elif garage.avg_repair_time_hours <= 6:
            score += 5
        
        if breakdown_type and garage.supported_services:
            if breakdown_type.lower() in garage.supported_services.lower():
                score += 25
        
        return round(max(0, score), 2)
