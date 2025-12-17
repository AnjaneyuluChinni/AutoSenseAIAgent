from database.models import Alert, get_db_session
from datetime import datetime

def get_user_alerts(user_id: int, include_read: bool = False) -> list:
    db = get_db_session()
    try:
        query = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_dismissed == False
        )
        
        if not include_read:
            query = query.filter(Alert.is_read == False)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        result = []
        for a in alerts:
            result.append({
                'id': a.id,
                'alert_type': a.alert_type,
                'title': a.title,
                'message': a.message,
                'priority': a.priority,
                'is_read': a.is_read,
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'vehicle_id': a.vehicle_id
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def mark_alert_read(alert_id: int) -> dict:
    db = get_db_session()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            db.close()
            return {"success": False, "error": "Alert not found"}
        
        alert.is_read = True
        db.commit()
        db.close()
        
        return {"success": True}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def dismiss_alert(alert_id: int) -> dict:
    db = get_db_session()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            db.close()
            return {"success": False, "error": "Alert not found"}
        
        alert.is_dismissed = True
        db.commit()
        db.close()
        
        return {"success": True}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def get_unread_count(user_id: int) -> int:
    db = get_db_session()
    try:
        count = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_read == False,
            Alert.is_dismissed == False
        ).count()
        
        db.close()
        return count
    except Exception as e:
        db.close()
        return 0

def get_all_alerts() -> list:
    db = get_db_session()
    try:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()
        
        result = []
        for a in alerts:
            result.append({
                'id': a.id,
                'user_id': a.user_id,
                'alert_type': a.alert_type,
                'title': a.title,
                'message': a.message,
                'priority': a.priority,
                'is_read': a.is_read,
                'is_dismissed': a.is_dismissed,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []
