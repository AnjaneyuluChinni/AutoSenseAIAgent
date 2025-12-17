from backend.agents.base_agent import BaseAgent
from datetime import datetime, timedelta
from database.models import Alert, get_db_session

class AlertAgent(BaseAgent):
    def __init__(self):
        super().__init__("AlertAgent")
    
    def execute(self, input_data: dict) -> dict:
        user_id = input_data.get('user_id')
        vehicle_id = input_data.get('vehicle_id')
        alert_type = input_data.get('alert_type')
        prediction_data = input_data.get('prediction_data', {})
        health_data = input_data.get('health_data', {})
        
        alerts_generated = []
        
        if prediction_data:
            urgency_score = prediction_data.get('urgency_score', 0)
            days_until_service = prediction_data.get('days_until_service', 999)
            
            if days_until_service <= 0:
                alerts_generated.append({
                    'type': 'overdue_service',
                    'title': 'Service Overdue!',
                    'message': f'Your vehicle service is overdue by {abs(days_until_service)} days. Please schedule immediately.',
                    'priority': 'critical'
                })
            elif days_until_service <= 7:
                alerts_generated.append({
                    'type': 'upcoming_service',
                    'title': 'Service Due Soon',
                    'message': f'Your vehicle service is due in {days_until_service} days. Book your slot now.',
                    'priority': 'high'
                })
            elif days_until_service <= 30:
                alerts_generated.append({
                    'type': 'upcoming_service',
                    'title': 'Service Reminder',
                    'message': f'Your next service is in {days_until_service} days.',
                    'priority': 'medium'
                })
        
        if health_data:
            engine_health = health_data.get('engine_health', 100)
            brake_health = health_data.get('brake_health', 100)
            battery_health = health_data.get('battery_health', 100)
            
            if engine_health < 50:
                alerts_generated.append({
                    'type': 'breakdown_risk',
                    'title': 'Engine Health Warning',
                    'message': f'Engine health is at {engine_health}%. Risk of breakdown. Get checked immediately.',
                    'priority': 'critical' if engine_health < 30 else 'high'
                })
            
            if brake_health < 50:
                alerts_generated.append({
                    'type': 'breakdown_risk',
                    'title': 'Brake System Warning',
                    'message': f'Brake health is at {brake_health}%. Immediate attention required for safety.',
                    'priority': 'critical' if brake_health < 30 else 'high'
                })
            
            if battery_health < 40:
                alerts_generated.append({
                    'type': 'breakdown_risk',
                    'title': 'Battery Warning',
                    'message': f'Battery health is at {battery_health}%. Risk of starting issues.',
                    'priority': 'high' if battery_health < 25 else 'medium'
                })
        
        if user_id and alerts_generated:
            try:
                db = get_db_session()
                for alert_data in alerts_generated:
                    alert = Alert(
                        user_id=user_id,
                        vehicle_id=vehicle_id,
                        alert_type=alert_data['type'],
                        title=alert_data['title'],
                        message=alert_data['message'],
                        priority=alert_data['priority'],
                        expires_at=datetime.now() + timedelta(days=7)
                    )
                    db.add(alert)
                db.commit()
                db.close()
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "alerts_generated": len(alerts_generated),
            "alerts": alerts_generated,
            "decision": f"Generated {len(alerts_generated)} alerts based on vehicle status"
        }
