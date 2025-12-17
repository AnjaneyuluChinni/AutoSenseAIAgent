from database.models import (
    Vehicle, ServiceRequest, BreakdownEvent, Garage, 
    Feedback, AgentLog, User, get_db_session
)
from backend.agents.orchestrator import MasterOrchestrator
from datetime import datetime, timedelta
from sqlalchemy import func
import pandas as pd

orchestrator = MasterOrchestrator()

def get_dashboard_stats() -> dict:
    db = get_db_session()
    try:
        total_vehicles = db.query(Vehicle).count()
        total_users = db.query(User).count()
        total_garages = db.query(Garage).filter(Garage.is_active == True).count()
        
        active_services = db.query(ServiceRequest).filter(
            ServiceRequest.status.in_(['open', 'in_progress'])
        ).count()
        
        active_breakdowns = db.query(BreakdownEvent).filter(
            BreakdownEvent.status.notin_(['completed'])
        ).count()
        
        completed_services = db.query(ServiceRequest).filter(
            ServiceRequest.status == 'completed'
        ).count()
        
        completed_breakdowns = db.query(BreakdownEvent).filter(
            BreakdownEvent.status == 'completed'
        ).count()
        
        breakdowns = db.query(BreakdownEvent).filter(
            BreakdownEvent.actual_repair_minutes != None
        ).all()
        
        avg_repair_time = 0
        if breakdowns:
            total_time = sum(b.actual_repair_minutes or 0 for b in breakdowns)
            avg_repair_time = total_time / len(breakdowns) if breakdowns else 0
        
        garages = db.query(Garage).filter(Garage.is_active == True).all()
        total_capacity = sum(g.capacity for g in garages)
        total_load = sum(g.current_load for g in garages)
        utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0
        
        db.close()
        
        return {
            "total_vehicles": total_vehicles,
            "total_users": total_users,
            "total_garages": total_garages,
            "active_services": active_services,
            "active_breakdowns": active_breakdowns,
            "completed_services": completed_services,
            "completed_breakdowns": completed_breakdowns,
            "avg_repair_time_minutes": round(avg_repair_time, 1),
            "garage_utilization_percent": round(utilization, 1)
        }
    except Exception as e:
        db.close()
        return {}

def get_breakdown_analytics() -> dict:
    db = get_db_session()
    try:
        breakdowns = db.query(BreakdownEvent).all()
        
        type_counts = {}
        for b in breakdowns:
            btype = b.breakdown_type or 'Unknown'
            type_counts[btype] = type_counts.get(btype, 0) + 1
        
        breakdown_data = [{'type': k, 'count': v} for k, v in type_counts.items()]
        breakdown_data.sort(key=lambda x: x['count'], reverse=True)
        
        monthly_counts = {}
        for b in breakdowns:
            if b.reported_at:
                month_key = b.reported_at.strftime('%Y-%m')
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        monthly_data = [{'month': k, 'count': v} for k, v in sorted(monthly_counts.items())]
        
        status_counts = {}
        for b in breakdowns:
            status = b.status or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        db.close()
        
        return {
            "by_type": breakdown_data,
            "by_month": monthly_data,
            "by_status": status_counts,
            "total_breakdowns": len(breakdowns)
        }
    except Exception as e:
        db.close()
        return {}

def get_service_analytics() -> dict:
    db = get_db_session()
    try:
        services = db.query(ServiceRequest).all()
        
        type_counts = {}
        for s in services:
            stype = s.service_type or 'Unknown'
            type_counts[stype] = type_counts.get(stype, 0) + 1
        
        monthly_counts = {}
        for s in services:
            if s.created_at:
                month_key = s.created_at.strftime('%Y-%m')
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        monthly_data = [{'month': k, 'count': v} for k, v in sorted(monthly_counts.items())]
        
        status_counts = {}
        for s in services:
            status = s.status or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        delays = []
        for s in services:
            if s.scheduled_date and s.completed_date:
                delay = (s.completed_date - s.scheduled_date).days
                if delay > 0:
                    delays.append(delay)
        
        avg_delay = sum(delays) / len(delays) if delays else 0
        
        db.close()
        
        return {
            "by_type": type_counts,
            "by_month": monthly_data,
            "by_status": status_counts,
            "total_services": len(services),
            "avg_delay_days": round(avg_delay, 1),
            "delayed_count": len(delays)
        }
    except Exception as e:
        db.close()
        return {}

def get_garage_performance() -> list:
    db = get_db_session()
    try:
        garages = db.query(Garage).filter(Garage.is_active == True).all()
        
        result = []
        for g in garages:
            breakdowns = db.query(BreakdownEvent).filter(
                BreakdownEvent.garage_id == g.id,
                BreakdownEvent.status == 'completed'
            ).all()
            
            services = db.query(ServiceRequest).filter(
                ServiceRequest.garage_id == g.id,
                ServiceRequest.status == 'completed'
            ).all()
            
            repair_times = [b.actual_repair_minutes for b in breakdowns if b.actual_repair_minutes]
            avg_repair = sum(repair_times) / len(repair_times) if repair_times else 0
            
            feedbacks = db.query(Feedback).filter(
                Feedback.service_request_id.in_([s.id for s in services])
            ).all()
            
            avg_rating = 0
            if feedbacks:
                ratings = [f.rating for f in feedbacks if f.rating]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            result.append({
                'garage': g.name,
                'garage_id': g.id,
                'total_breakdowns': len(breakdowns),
                'total_services': len(services),
                'avg_repair_time': round(avg_repair, 1),
                'avg_rating': round(avg_rating, 1) if avg_rating else g.rating,
                'capacity': g.capacity,
                'current_load': g.current_load,
                'utilization': round(g.current_load / g.capacity * 100, 1) if g.capacity > 0 else 0
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_agent_logs(limit: int = 100) -> list:
    db = get_db_session()
    try:
        logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                'id': log.id,
                'agent_name': log.agent_name,
                'action': log.action,
                'decision': log.decision,
                'success': log.success,
                'error_message': log.error_message,
                'execution_time_ms': log.execution_time_ms,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_user_service_history(user_id: int) -> list:
    db = get_db_session()
    try:
        vehicles = db.query(Vehicle).filter(Vehicle.owner_id == user_id).all()
        vehicle_ids = [v.id for v in vehicles]
        
        services = db.query(ServiceRequest).filter(
            ServiceRequest.vehicle_id.in_(vehicle_ids)
        ).order_by(ServiceRequest.created_at.desc()).all()
        
        result = []
        for s in services:
            vehicle = next((v for v in vehicles if v.id == s.vehicle_id), None)
            result.append({
                'id': s.id,
                'vehicle': f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown',
                'service_type': s.service_type,
                'status': s.status,
                'date': s.scheduled_date.strftime('%Y-%m-%d') if s.scheduled_date else 'N/A',
                'cost': s.actual_cost or s.estimated_cost or 0
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []
