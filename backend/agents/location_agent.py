from backend.agents.base_agent import BaseAgent
from datetime import datetime
import random
import math

class LocationTrackingAgent(BaseAgent):
    def __init__(self):
        super().__init__("LocationTrackingAgent")
    
    def execute(self, input_data: dict) -> dict:
        action = input_data.get('action', 'track')
        
        if action == 'track_vehicle':
            return self.track_vehicle(input_data)
        elif action == 'track_garage':
            return self.track_garage_movement(input_data)
        elif action == 'simulate_movement':
            return self.simulate_movement(input_data)
        else:
            return self.get_current_location(input_data)
    
    def get_current_location(self, input_data: dict) -> dict:
        latitude = input_data.get('latitude', 28.6139)
        longitude = input_data.get('longitude', 77.2090)
        
        lat_offset = random.uniform(-0.001, 0.001)
        lng_offset = random.uniform(-0.001, 0.001)
        
        return {
            "success": True,
            "latitude": latitude + lat_offset,
            "longitude": longitude + lng_offset,
            "accuracy_meters": random.randint(5, 20),
            "timestamp": datetime.now().isoformat(),
            "decision": "Retrieved current location with GPS simulation"
        }
    
    def track_vehicle(self, input_data: dict) -> dict:
        vehicle_id = input_data.get('vehicle_id')
        current_lat = input_data.get('latitude', 28.6139)
        current_lng = input_data.get('longitude', 77.2090)
        
        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "location": {
                "latitude": current_lat,
                "longitude": current_lng
            },
            "speed_kmh": 0,
            "heading": 0,
            "status": "stationary",
            "last_updated": datetime.now().isoformat(),
            "decision": f"Tracking vehicle #{vehicle_id} - currently stationary"
        }
    
    def track_garage_movement(self, input_data: dict) -> dict:
        garage_lat = input_data.get('garage_latitude')
        garage_lng = input_data.get('garage_longitude')
        vehicle_lat = input_data.get('vehicle_latitude')
        vehicle_lng = input_data.get('vehicle_longitude')
        progress_percent = input_data.get('progress_percent', 0)
        
        if all([garage_lat, garage_lng, vehicle_lat, vehicle_lng]):
            current_lat = garage_lat + (vehicle_lat - garage_lat) * (progress_percent / 100)
            current_lng = garage_lng + (vehicle_lng - garage_lng) * (progress_percent / 100)
            
            return {
                "success": True,
                "current_location": {
                    "latitude": current_lat,
                    "longitude": current_lng
                },
                "progress_percent": progress_percent,
                "remaining_distance_km": self.calculate_distance(
                    current_lat, current_lng, vehicle_lat, vehicle_lng
                ),
                "estimated_speed_kmh": 30,
                "decision": f"Garage vehicle at {progress_percent}% of journey"
            }
        
        return {
            "success": False,
            "error": "Missing location coordinates"
        }
    
    def simulate_movement(self, input_data: dict) -> dict:
        start_lat = input_data.get('start_latitude')
        start_lng = input_data.get('start_longitude')
        end_lat = input_data.get('end_latitude')
        end_lng = input_data.get('end_longitude')
        steps = input_data.get('steps', 10)
        
        if not all([start_lat, start_lng, end_lat, end_lng]):
            return {"success": False, "error": "Missing coordinates"}
        
        path = []
        for i in range(steps + 1):
            progress = i / steps
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            
            lat += random.uniform(-0.0005, 0.0005)
            lng += random.uniform(-0.0005, 0.0005)
            
            path.append({
                "step": i,
                "latitude": lat,
                "longitude": lng,
                "progress_percent": progress * 100
            })
        
        return {
            "success": True,
            "path": path,
            "total_distance_km": self.calculate_distance(start_lat, start_lng, end_lat, end_lng),
            "decision": f"Generated {steps}-step movement path"
        }
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return round(R * c, 2)
