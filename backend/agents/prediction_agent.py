from backend.agents.base_agent import BaseAgent
from datetime import datetime, timedelta
import numpy as np

class PredictionAgent(BaseAgent):
    def __init__(self):
        super().__init__("PredictionAgent")
    
    def execute(self, input_data: dict) -> dict:
        last_service_date = input_data.get('last_service_date')
        avg_km_per_month = input_data.get('avg_km_per_month', 1000)
        service_interval_km = input_data.get('service_interval_km', 10000)
        service_interval_months = input_data.get('service_interval_months', 6)
        breakdown_count = input_data.get('breakdown_count', 0)
        engine_health = input_data.get('engine_health', 100)
        brake_health = input_data.get('brake_health', 100)
        battery_health = input_data.get('battery_health', 100)
        
        if isinstance(last_service_date, str):
            last_service_date = datetime.fromisoformat(last_service_date)
        elif last_service_date is None:
            last_service_date = datetime.now() - timedelta(days=180)
        
        months_to_km_limit = service_interval_km / avg_km_per_month if avg_km_per_month > 0 else 12
        
        predicted_months = min(months_to_km_limit, service_interval_months)
        
        health_factor = (engine_health + brake_health + battery_health) / 300
        breakdown_penalty = breakdown_count * 0.5
        
        adjusted_months = predicted_months * health_factor - breakdown_penalty
        adjusted_months = max(0.5, adjusted_months)
        
        next_service_date = last_service_date + timedelta(days=int(adjusted_months * 30))
        
        days_until_service = (next_service_date - datetime.now()).days
        
        if days_until_service <= 0:
            urgency_score = 100
        elif days_until_service <= 7:
            urgency_score = 90
        elif days_until_service <= 14:
            urgency_score = 75
        elif days_until_service <= 30:
            urgency_score = 50
        elif days_until_service <= 60:
            urgency_score = 25
        else:
            urgency_score = 10
        
        urgency_score = min(100, urgency_score + (100 - min(engine_health, brake_health, battery_health)) * 0.3)
        
        confidence = 0.85 - (breakdown_count * 0.05)
        confidence = max(0.5, min(0.95, confidence))
        
        if urgency_score >= 75:
            alert_trigger = "critical"
        elif urgency_score >= 50:
            alert_trigger = "high"
        elif urgency_score >= 25:
            alert_trigger = "medium"
        else:
            alert_trigger = "low"
        
        return {
            "success": True,
            "predicted_service_date": next_service_date.isoformat(),
            "days_until_service": days_until_service,
            "urgency_score": round(urgency_score, 2),
            "confidence_score": round(confidence, 2),
            "alert_trigger": alert_trigger,
            "decision": f"Predicted next service in {days_until_service} days with {urgency_score:.0f}% urgency",
            "factors": {
                "health_factor": round(health_factor, 2),
                "breakdown_penalty": breakdown_penalty,
                "adjusted_interval_months": round(adjusted_months, 1)
            }
        }
