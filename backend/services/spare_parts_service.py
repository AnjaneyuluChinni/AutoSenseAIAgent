from database.models import SparePart, get_db_session
from backend.agents.orchestrator import MasterOrchestrator

orchestrator = MasterOrchestrator()

def get_all_spare_parts() -> list:
    db = get_db_session()
    try:
        parts = db.query(SparePart).all()
        
        result = []
        for p in parts:
            result.append({
                'id': p.id,
                'part_number': p.part_number,
                'name': p.name,
                'category': p.category,
                'oem_price': p.oem_price,
                'aftermarket_price': p.aftermarket_price,
                'quantity_in_stock': p.quantity_in_stock,
                'minimum_stock': p.minimum_stock,
                'in_stock': p.quantity_in_stock > 0,
                'low_stock': p.quantity_in_stock <= p.minimum_stock,
                'compatible_makes': p.compatible_makes,
                'compatible_models': p.compatible_models,
                'breakdown_types': p.breakdown_types
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []

def get_parts_for_breakdown(breakdown_type: str, vehicle_make: str = None, 
                           vehicle_model: str = None) -> dict:
    pricing_agent = orchestrator.get_agent('pricing')
    
    input_data = {
        'breakdown_type': breakdown_type,
        'vehicle_make': vehicle_make or '',
        'vehicle_model': vehicle_model or '',
        'include_parts': True
    }
    
    return pricing_agent.run(input_data)

def add_spare_part(part_number: str, name: str, category: str, oem_price: float,
                   aftermarket_price: float = None, quantity: int = 0,
                   minimum_stock: int = 5, compatible_makes: str = None,
                   compatible_models: str = None, breakdown_types: str = None) -> dict:
    db = get_db_session()
    try:
        existing = db.query(SparePart).filter(SparePart.part_number == part_number).first()
        if existing:
            db.close()
            return {"success": False, "error": "Part number already exists"}
        
        part = SparePart(
            part_number=part_number,
            name=name,
            category=category,
            oem_price=oem_price,
            aftermarket_price=aftermarket_price,
            quantity_in_stock=quantity,
            minimum_stock=minimum_stock,
            compatible_makes=compatible_makes,
            compatible_models=compatible_models,
            breakdown_types=breakdown_types
        )
        
        db.add(part)
        db.commit()
        part_id = part.id
        db.close()
        
        return {"success": True, "part_id": part_id}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def update_spare_part(part_id: int, **kwargs) -> dict:
    db = get_db_session()
    try:
        part = db.query(SparePart).filter(SparePart.id == part_id).first()
        if not part:
            db.close()
            return {"success": False, "error": "Part not found"}
        
        for key, value in kwargs.items():
            if hasattr(part, key) and value is not None:
                setattr(part, key, value)
        
        db.commit()
        db.close()
        
        return {"success": True, "message": "Part updated successfully"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def update_stock(part_id: int, quantity_change: int) -> dict:
    db = get_db_session()
    try:
        part = db.query(SparePart).filter(SparePart.id == part_id).first()
        if not part:
            db.close()
            return {"success": False, "error": "Part not found"}
        
        new_quantity = part.quantity_in_stock + quantity_change
        if new_quantity < 0:
            db.close()
            return {"success": False, "error": "Insufficient stock"}
        
        part.quantity_in_stock = new_quantity
        db.commit()
        db.close()
        
        return {"success": True, "new_quantity": new_quantity}
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "error": str(e)}

def get_low_stock_parts() -> list:
    db = get_db_session()
    try:
        parts = db.query(SparePart).filter(
            SparePart.quantity_in_stock <= SparePart.minimum_stock
        ).all()
        
        result = []
        for p in parts:
            result.append({
                'id': p.id,
                'part_number': p.part_number,
                'name': p.name,
                'category': p.category,
                'quantity_in_stock': p.quantity_in_stock,
                'minimum_stock': p.minimum_stock,
                'oem_price': p.oem_price
            })
        
        db.close()
        return result
    except Exception as e:
        db.close()
        return []
