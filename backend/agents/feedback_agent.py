from backend.agents.base_agent import BaseAgent
from database.models import Feedback, ServiceRequest, BreakdownEvent, Garage, get_db_session
from sqlalchemy import func
import pandas as pd

class FeedbackRCAAgent(BaseAgent):
    def __init__(self):
        super().__init__("FeedbackRCAAgent")
    
    def execute(self, input_data: dict) -> dict:
        action = input_data.get('action', 'analyze')
        
        if action == 'submit':
            return self.submit_feedback(input_data)
        elif action == 'analyze':
            return self.analyze_feedback(input_data)
        elif action == 'rca':
            return self.perform_rca(input_data)
        elif action == 'insights':
            return self.get_oem_insights(input_data)
        else:
            return {"success": False, "error": "Unknown action"}
    
    def submit_feedback(self, input_data: dict) -> dict:
        user_id = input_data.get('user_id')
        service_request_id = input_data.get('service_request_id')
        breakdown_event_id = input_data.get('breakdown_event_id')
        rating = input_data.get('rating', 5)
        comment = input_data.get('comment', '')
        service_quality = input_data.get('service_quality', 5)
        time_satisfaction = input_data.get('time_satisfaction', 5)
        cost_satisfaction = input_data.get('cost_satisfaction', 5)
        would_recommend = input_data.get('would_recommend', True)
        
        db = get_db_session()
        
        try:
            feedback = Feedback(
                user_id=user_id,
                service_request_id=service_request_id,
                breakdown_event_id=breakdown_event_id,
                rating=rating,
                comment=comment,
                service_quality=service_quality,
                time_satisfaction=time_satisfaction,
                cost_satisfaction=cost_satisfaction,
                would_recommend=would_recommend
            )
            
            db.add(feedback)
            db.commit()
            
            feedback_id = feedback.id
            db.close()
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "decision": f"Submitted feedback with rating {rating}/5"
            }
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "error": str(e)}
    
    def analyze_feedback(self, input_data: dict) -> dict:
        garage_id = input_data.get('garage_id')
        days = input_data.get('days', 30)
        
        db = get_db_session()
        
        try:
            query = db.query(Feedback)
            
            feedbacks = query.all()
            
            if not feedbacks:
                db.close()
                return {
                    "success": True,
                    "message": "No feedback data available",
                    "decision": "No feedback to analyze"
                }
            
            total = len(feedbacks)
            avg_rating = sum(f.rating or 0 for f in feedbacks) / total
            avg_service = sum(f.service_quality or 0 for f in feedbacks) / total
            avg_time = sum(f.time_satisfaction or 0 for f in feedbacks) / total
            avg_cost = sum(f.cost_satisfaction or 0 for f in feedbacks) / total
            recommend_pct = sum(1 for f in feedbacks if f.would_recommend) / total * 100
            
            rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for f in feedbacks:
                if f.rating:
                    rating_dist[f.rating] = rating_dist.get(f.rating, 0) + 1
            
            db.close()
            
            return {
                "success": True,
                "total_feedback": total,
                "averages": {
                    "overall_rating": round(avg_rating, 2),
                    "service_quality": round(avg_service, 2),
                    "time_satisfaction": round(avg_time, 2),
                    "cost_satisfaction": round(avg_cost, 2)
                },
                "recommendation_rate": round(recommend_pct, 1),
                "rating_distribution": rating_dist,
                "decision": f"Analyzed {total} feedback entries, avg rating: {avg_rating:.1f}/5"
            }
            
        except Exception as e:
            db.close()
            return {"success": False, "error": str(e)}
    
    def perform_rca(self, input_data: dict) -> dict:
        db = get_db_session()
        
        try:
            breakdown_counts = {}
            breakdowns = db.query(BreakdownEvent).all()
            
            for b in breakdowns:
                btype = b.breakdown_type or 'Unknown'
                breakdown_counts[btype] = breakdown_counts.get(btype, 0) + 1
            
            sorted_breakdowns = sorted(breakdown_counts.items(), key=lambda x: x[1], reverse=True)
            
            service_delays = []
            services = db.query(ServiceRequest).filter(
                ServiceRequest.scheduled_date != None,
                ServiceRequest.completed_date != None
            ).all()
            
            for s in services:
                if s.scheduled_date and s.completed_date:
                    delay_days = (s.completed_date - s.scheduled_date).days
                    if delay_days > 0:
                        service_delays.append({
                            'service_id': s.id,
                            'delay_days': delay_days,
                            'service_type': s.service_type
                        })
            
            garages = db.query(Garage).all()
            garage_metrics = []
            
            for g in garages:
                garage_breakdowns = db.query(BreakdownEvent).filter(
                    BreakdownEvent.garage_id == g.id
                ).all()
                
                avg_repair = 0
                if garage_breakdowns:
                    repair_times = [b.actual_repair_minutes for b in garage_breakdowns if b.actual_repair_minutes]
                    if repair_times:
                        avg_repair = sum(repair_times) / len(repair_times)
                
                garage_metrics.append({
                    'garage_id': g.id,
                    'name': g.name,
                    'total_breakdowns': len(garage_breakdowns),
                    'avg_repair_minutes': round(avg_repair, 1),
                    'rating': g.rating
                })
            
            db.close()
            
            insights = []
            if sorted_breakdowns:
                top_issue = sorted_breakdowns[0]
                insights.append(f"Most common breakdown: {top_issue[0]} ({top_issue[1]} occurrences)")
            
            if service_delays:
                avg_delay = sum(d['delay_days'] for d in service_delays) / len(service_delays)
                insights.append(f"Average service delay: {avg_delay:.1f} days")
            
            return {
                "success": True,
                "breakdown_analysis": {
                    "by_type": dict(sorted_breakdowns[:10]),
                    "total_breakdowns": len(breakdowns)
                },
                "service_analysis": {
                    "total_delayed": len(service_delays),
                    "delays": service_delays[:10]
                },
                "garage_analysis": garage_metrics,
                "key_insights": insights,
                "decision": f"RCA complete: {len(insights)} insights generated"
            }
            
        except Exception as e:
            db.close()
            return {"success": False, "error": str(e)}
    
    def get_oem_insights(self, input_data: dict) -> dict:
        db = get_db_session()
        
        try:
            from database.models import Vehicle
            vehicles = db.query(Vehicle).all()
            
            make_issues = {}
            for v in vehicles:
                make = v.make or 'Unknown'
                breakdowns = db.query(BreakdownEvent).filter(
                    BreakdownEvent.vehicle_id == v.id
                ).count()
                
                if make not in make_issues:
                    make_issues[make] = {'count': 0, 'breakdowns': 0}
                make_issues[make]['count'] += 1
                make_issues[make]['breakdowns'] += breakdowns
            
            for make in make_issues:
                if make_issues[make]['count'] > 0:
                    make_issues[make]['avg_breakdowns'] = round(
                        make_issues[make]['breakdowns'] / make_issues[make]['count'], 2
                    )
            
            health_concerns = []
            for v in vehicles:
                if v.engine_health and v.engine_health < 50:
                    health_concerns.append({
                        'vehicle_id': v.id,
                        'make': v.make,
                        'model': v.model,
                        'concern': 'Engine Health Critical',
                        'value': v.engine_health
                    })
                if v.brake_health and v.brake_health < 50:
                    health_concerns.append({
                        'vehicle_id': v.id,
                        'make': v.make,
                        'model': v.model,
                        'concern': 'Brake Health Critical',
                        'value': v.brake_health
                    })
            
            db.close()
            
            return {
                "success": True,
                "manufacturer_insights": make_issues,
                "health_concerns": health_concerns[:20],
                "total_vehicles_analyzed": len(vehicles),
                "decision": f"Generated OEM insights for {len(make_issues)} manufacturers"
            }
            
        except Exception as e:
            db.close()
            return {"success": False, "error": str(e)}
