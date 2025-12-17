from backend.agents.base_agent import BaseAgent
from backend.agents.prediction_agent import PredictionAgent
from backend.agents.alert_agent import AlertAgent
from backend.agents.scheduling_agent import SchedulingAgent
from backend.agents.breakdown_agent import BreakdownAgent
from backend.agents.location_agent import LocationTrackingAgent
from backend.agents.garage_recommendation_agent import GarageRecommendationAgent
from backend.agents.eta_agent import ETAEstimationAgent
from backend.agents.pricing_agent import PricingAgent
from backend.agents.visualization_agent import VisualizationAgent
from backend.agents.feedback_agent import FeedbackRCAAgent

class MasterOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__("MasterOrchestrator")
        
        self.agents = {
            'prediction': PredictionAgent(),
            'alert': AlertAgent(),
            'scheduling': SchedulingAgent(),
            'breakdown': BreakdownAgent(),
            'location': LocationTrackingAgent(),
            'garage_recommendation': GarageRecommendationAgent(),
            'eta': ETAEstimationAgent(),
            'pricing': PricingAgent(),
            'visualization': VisualizationAgent(),
            'feedback': FeedbackRCAAgent()
        }
    
    def execute(self, input_data: dict) -> dict:
        task_type = input_data.get('task_type')
        
        if task_type == 'predict_service':
            return self.handle_prediction(input_data)
        elif task_type == 'schedule_service':
            return self.handle_scheduling(input_data)
        elif task_type == 'breakdown_emergency':
            return self.handle_breakdown(input_data)
        elif task_type == 'get_alerts':
            return self.handle_alerts(input_data)
        elif task_type == 'analyze_feedback':
            return self.handle_feedback_analysis(input_data)
        elif task_type == 'generate_visualization':
            return self.handle_visualization(input_data)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
    
    def handle_prediction(self, input_data: dict) -> dict:
        prediction_result = self.agents['prediction'].run(input_data)
        
        if prediction_result.get('success'):
            alert_input = {
                'user_id': input_data.get('user_id'),
                'vehicle_id': input_data.get('vehicle_id'),
                'prediction_data': prediction_result,
                'health_data': {
                    'engine_health': input_data.get('engine_health', 100),
                    'brake_health': input_data.get('brake_health', 100),
                    'battery_health': input_data.get('battery_health', 100)
                }
            }
            alert_result = self.agents['alert'].run(alert_input)
            
            return {
                "success": True,
                "prediction": prediction_result,
                "alerts": alert_result,
                "decision": "Completed prediction and alert generation"
            }
        
        return prediction_result
    
    def handle_scheduling(self, input_data: dict) -> dict:
        scheduling_result = self.agents['scheduling'].run(input_data)
        return scheduling_result
    
    def handle_breakdown(self, input_data: dict) -> dict:
        breakdown_result = self.agents['breakdown'].run(input_data)
        
        if not breakdown_result.get('success'):
            return breakdown_result
        
        garage_input = {
            'latitude': input_data.get('latitude'),
            'longitude': input_data.get('longitude'),
            'breakdown_type': input_data.get('breakdown_type'),
            'limit': 5
        }
        garage_result = self.agents['garage_recommendation'].run(garage_input)
        
        eta_results = []
        pricing_results = []
        
        if garage_result.get('success') and garage_result.get('recommendations'):
            for garage in garage_result['recommendations'][:3]:
                eta_input = {
                    'garage_latitude': garage['latitude'],
                    'garage_longitude': garage['longitude'],
                    'vehicle_latitude': input_data.get('latitude'),
                    'vehicle_longitude': input_data.get('longitude'),
                    'breakdown_type': input_data.get('breakdown_type')
                }
                eta = self.agents['eta'].run(eta_input)
                eta_results.append({
                    'garage_id': garage['id'],
                    'garage_name': garage['name'],
                    'eta': eta
                })
            
            pricing_input = {
                'breakdown_type': input_data.get('breakdown_type'),
                'vehicle_make': input_data.get('vehicle_make', ''),
                'vehicle_model': input_data.get('vehicle_model', '')
            }
            pricing_result = self.agents['pricing'].run(pricing_input)
            pricing_results = pricing_result
        
        return {
            "success": True,
            "breakdown_event": breakdown_result,
            "nearby_garages": garage_result,
            "eta_estimates": eta_results,
            "cost_estimate": pricing_results,
            "decision": "Breakdown handled - garages found with ETAs and pricing"
        }
    
    def handle_alerts(self, input_data: dict) -> dict:
        return self.agents['alert'].run(input_data)
    
    def handle_feedback_analysis(self, input_data: dict) -> dict:
        return self.agents['feedback'].run(input_data)
    
    def handle_visualization(self, input_data: dict) -> dict:
        return self.agents['visualization'].run(input_data)
    
    def get_agent(self, agent_name: str):
        return self.agents.get(agent_name)
