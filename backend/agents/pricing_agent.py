from backend.agents.base_agent import BaseAgent
from database.models import SparePart, get_db_session

class PricingAgent(BaseAgent):
    def __init__(self):
        super().__init__("PricingAgent")
        
        self.base_labor_rates = {
            'flat_tire': 200,
            'tire': 200,
            'battery': 300,
            'battery_dead': 150,
            'engine': 2000,
            'engine_failure': 3000,
            'overheating': 800,
            'brake': 1000,
            'brake_failure': 1200,
            'electrical': 600,
            'fuel': 100,
            'out_of_fuel': 50,
            'transmission': 2500,
            'coolant': 400,
            'oil_leak': 700,
            'starter': 500,
            'alternator': 800,
            'general': 500,
            'regular_service': 1500
        }
    
    def execute(self, input_data: dict) -> dict:
        breakdown_type = input_data.get('breakdown_type', 'general')
        vehicle_make = input_data.get('vehicle_make', '')
        vehicle_model = input_data.get('vehicle_model', '')
        include_parts = input_data.get('include_parts', True)
        
        labor_cost = self.get_labor_cost(breakdown_type)
        
        parts_info = []
        parts_total = 0
        
        if include_parts:
            parts_result = self.get_required_parts(breakdown_type, vehicle_make, vehicle_model)
            parts_info = parts_result['parts']
            parts_total = parts_result['total']
        
        subtotal = labor_cost + parts_total
        tax = subtotal * 0.18
        total = subtotal + tax
        
        return {
            "success": True,
            "breakdown_type": breakdown_type,
            "cost_breakdown": {
                "labor": {
                    "description": f"Labor charges for {breakdown_type}",
                    "amount": labor_cost
                },
                "parts": parts_info,
                "parts_total": parts_total,
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "tax_rate": "18%",
                "total": round(total, 2)
            },
            "currency": "INR",
            "estimate_validity_hours": 24,
            "decision": f"Estimated total cost: ₹{round(total, 2)} for {breakdown_type}"
        }
    
    def get_labor_cost(self, breakdown_type: str) -> float:
        breakdown_lower = breakdown_type.lower().replace(' ', '_')
        
        for key, cost in self.base_labor_rates.items():
            if key in breakdown_lower or breakdown_lower in key:
                return cost
        
        return self.base_labor_rates['general']
    
    def get_required_parts(self, breakdown_type: str, vehicle_make: str, vehicle_model: str) -> dict:
        parts_mapping = {
            'flat_tire': [('Tire', 3500), ('Tube', 500)],
            'tire': [('Tire', 3500), ('Tube', 500)],
            'battery': [('Battery 12V', 5000)],
            'battery_dead': [('Battery 12V', 5000)],
            'brake': [('Brake Pads Set', 2500), ('Brake Fluid', 400)],
            'brake_failure': [('Brake Pads Set', 2500), ('Brake Disc', 3000), ('Brake Fluid', 400)],
            'engine': [('Engine Oil 5L', 2500), ('Oil Filter', 350), ('Air Filter', 450)],
            'overheating': [('Coolant 2L', 600), ('Thermostat', 1200), ('Radiator Hose', 800)],
            'electrical': [('Fuse Kit', 300), ('Wiring Harness', 1500)],
            'oil_leak': [('Oil Gasket Set', 800), ('Engine Oil 5L', 2500)],
            'coolant': [('Coolant 2L', 600), ('Radiator Cap', 200)],
            'starter': [('Starter Motor', 4500)],
            'alternator': [('Alternator', 6000), ('Belt', 800)],
            'transmission': [('Transmission Fluid', 1200), ('Clutch Kit', 8000)],
            'regular_service': [('Engine Oil 5L', 2500), ('Oil Filter', 350), ('Air Filter', 450), ('Spark Plugs Set', 600)]
        }
        
        db = get_db_session()
        
        try:
            breakdown_lower = breakdown_type.lower().replace(' ', '_')
            default_parts = []
            
            for key, parts in parts_mapping.items():
                if key in breakdown_lower or breakdown_lower in key:
                    default_parts = parts
                    break
            
            parts_info = []
            total = 0
            
            for part_name, default_price in default_parts:
                db_part = db.query(SparePart).filter(
                    SparePart.name.ilike(f"%{part_name}%")
                ).first()
                
                if db_part:
                    price = db_part.oem_price
                    in_stock = db_part.quantity_in_stock > 0
                else:
                    price = default_price
                    in_stock = True
                
                parts_info.append({
                    "name": part_name,
                    "oem_price": price,
                    "in_stock": in_stock,
                    "quantity": 1
                })
                total += price
            
            db.close()
            
            return {
                "parts": parts_info,
                "total": total
            }
            
        except Exception as e:
            db.close()
            return {"parts": [], "total": 0}
