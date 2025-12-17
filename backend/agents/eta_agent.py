from backend.agents.base_agent import BaseAgent
import math
import random

class ETAEstimationAgent(BaseAgent):
    def __init__(self):
        super().__init__("ETAEstimationAgent")
        
        self.avg_city_speed_kmh = 25
        self.avg_highway_speed_kmh = 60
    
    def execute(self, input_data: dict) -> dict:
        garage_lat = input_data.get('garage_latitude')
        garage_lng = input_data.get('garage_longitude')
        vehicle_lat = input_data.get('vehicle_latitude')
        vehicle_lng = input_data.get('vehicle_longitude')
        breakdown_type = input_data.get('breakdown_type', 'General')
        
        if not all([garage_lat, garage_lng, vehicle_lat, vehicle_lng]):
            return {
                "success": False,
                "error": "Missing location coordinates"
            }
        
        distance_km = self.calculate_distance(garage_lat, garage_lng, vehicle_lat, vehicle_lng)
        
        arrival_minutes = self.estimate_arrival_time(distance_km)
        
        repair_minutes = self.estimate_repair_time(breakdown_type)
        
        total_time = arrival_minutes + repair_minutes
        
        confidence = self.calculate_confidence(distance_km, breakdown_type)
        
        return {
            "success": True,
            "distance_km": distance_km,
            "estimated_arrival_minutes": arrival_minutes,
            "estimated_repair_minutes": repair_minutes,
            "total_estimated_minutes": total_time,
            "confidence_score": confidence,
            "breakdown": {
                "travel_time": arrival_minutes,
                "repair_time": repair_minutes,
                "buffer_time": int(total_time * 0.1)
            },
            "formatted": {
                "arrival": self.format_time(arrival_minutes),
                "repair": self.format_time(repair_minutes),
                "total": self.format_time(total_time)
            },
            "decision": f"ETA: {self.format_time(arrival_minutes)} arrival, {self.format_time(repair_minutes)} repair"
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
    
    def estimate_arrival_time(self, distance_km: float) -> int:
        if distance_km <= 5:
            speed = self.avg_city_speed_kmh
        elif distance_km <= 15:
            speed = (self.avg_city_speed_kmh + self.avg_highway_speed_kmh) / 2
        else:
            speed = self.avg_highway_speed_kmh
        
        base_time = (distance_km / speed) * 60
        
        traffic_factor = random.uniform(1.0, 1.3)
        
        prep_time = 5
        
        return int(base_time * traffic_factor + prep_time)
    
    def estimate_repair_time(self, breakdown_type: str) -> int:
        repair_times = {
            'flat_tire': 30,
            'tire': 30,
            'battery': 45,
            'battery_dead': 45,
            'engine': 180,
            'engine_failure': 180,
            'overheating': 90,
            'brake': 120,
            'brake_failure': 150,
            'electrical': 90,
            'fuel': 30,
            'out_of_fuel': 20,
            'transmission': 240,
            'coolant': 60,
            'oil_leak': 90,
            'starter': 60,
            'alternator': 120,
            'general': 60,
            'unknown': 90
        }
        
        breakdown_lower = breakdown_type.lower().replace(' ', '_')
        
        for key, time in repair_times.items():
            if key in breakdown_lower or breakdown_lower in key:
                variance = random.uniform(0.8, 1.2)
                return int(time * variance)
        
        return int(repair_times['general'] * random.uniform(0.9, 1.3))
    
    def calculate_confidence(self, distance_km: float, breakdown_type: str) -> float:
        base_confidence = 0.85
        
        if distance_km > 20:
            base_confidence -= 0.1
        elif distance_km > 10:
            base_confidence -= 0.05
        
        known_types = ['tire', 'battery', 'engine', 'brake', 'fuel', 'electrical']
        breakdown_lower = breakdown_type.lower()
        
        if any(t in breakdown_lower for t in known_types):
            base_confidence += 0.05
        else:
            base_confidence -= 0.1
        
        return round(max(0.5, min(0.95, base_confidence)), 2)
    
    def format_time(self, minutes: int) -> str:
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hr"
            return f"{hours} hr {mins} min"
