from database.models import (
    User, Vehicle, Garage, ServiceSlot, ServiceRequest,
    BreakdownEvent, SparePart, Alert, Feedback, init_db, get_db_session
)
from utils.auth import hash_password
from datetime import datetime, timedelta
import random

def seed_database():
    init_db()
    db = get_db_session()
    
    existing_user = db.query(User).first()
    if existing_user:
        print("Database already seeded. Skipping...")
        db.close()
        return
    
    print("Seeding database with demo data...")
    
    users = [
        User(
            username="john_user",
            email="john@example.com",
            password_hash=hash_password("password123"),
            full_name="John Smith",
            phone="+91-9876543210",
            role="user"
        ),
        User(
            username="sarah_user",
            email="sarah@example.com",
            password_hash=hash_password("password123"),
            full_name="Sarah Johnson",
            phone="+91-9876543211",
            role="user"
        ),
        User(
            username="mike_user",
            email="mike@example.com",
            password_hash=hash_password("password123"),
            full_name="Mike Wilson",
            phone="+91-9876543212",
            role="user"
        ),
        User(
            username="admin",
            email="admin@autosense.com",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            phone="+91-9876543200",
            role="admin"
        ),
        User(
            username="manager",
            email="manager@autosense.com",
            password_hash=hash_password("manager123"),
            full_name="Service Manager",
            phone="+91-9876543201",
            role="admin"
        )
    ]
    
    for user in users:
        db.add(user)
    db.commit()
    
    garages = [
        Garage(
            name="AutoCare Express - Delhi",
            address="45 MG Road, Connaught Place",
            city="New Delhi",
            latitude=28.6315,
            longitude=77.2167,
            phone="+91-11-23456789",
            email="delhi@autocare.com",
            capacity=15,
            current_load=8,
            opening_time="08:00",
            closing_time="20:00",
            working_days="Mon-Sun",
            supported_services="Engine,Brake,Battery,Tire,Electrical,General Service",
            rating=4.5,
            avg_repair_time_hours=2.5
        ),
        Garage(
            name="QuickFix Motors - Gurgaon",
            address="Sector 29, Near IFFCO Chowk",
            city="Gurgaon",
            latitude=28.4595,
            longitude=77.0266,
            phone="+91-124-4567890",
            email="gurgaon@quickfix.com",
            capacity=12,
            current_load=5,
            opening_time="09:00",
            closing_time="19:00",
            working_days="Mon-Sat",
            supported_services="Engine,Brake,Transmission,Battery,AC",
            rating=4.2,
            avg_repair_time_hours=3.0
        ),
        Garage(
            name="Hero Service Center - Noida",
            address="Sector 18, Near Atta Market",
            city="Noida",
            latitude=28.5707,
            longitude=77.3219,
            phone="+91-120-5678901",
            email="noida@heroservice.com",
            capacity=20,
            current_load=12,
            opening_time="08:00",
            closing_time="18:00",
            working_days="Mon-Sat",
            supported_services="All Services,Engine,Brake,Battery,Tire,Body Work",
            rating=4.7,
            avg_repair_time_hours=2.0
        ),
        Garage(
            name="M&M Authorized - South Delhi",
            address="Greater Kailash II, M Block",
            city="New Delhi",
            latitude=28.5355,
            longitude=77.2426,
            phone="+91-11-26789012",
            email="gk2@mmservice.com",
            capacity=18,
            current_load=10,
            opening_time="09:00",
            closing_time="19:00",
            working_days="Mon-Sun",
            supported_services="Engine,Brake,Electrical,Suspension,General",
            rating=4.6,
            avg_repair_time_hours=2.2
        ),
        Garage(
            name="24x7 Roadside Assist - Central",
            address="ITO, Ring Road",
            city="New Delhi",
            latitude=28.6289,
            longitude=77.2413,
            phone="+91-11-27890123",
            email="emergency@roadside247.com",
            capacity=10,
            current_load=3,
            opening_time="00:00",
            closing_time="23:59",
            working_days="Mon-Sun",
            supported_services="Emergency,Tire,Battery,Towing,Fuel",
            rating=4.3,
            avg_repair_time_hours=1.5
        )
    ]
    
    for garage in garages:
        db.add(garage)
    db.commit()
    
    for garage in garages:
        for i in range(14):
            date = datetime.now() + timedelta(days=i)
            for slot_time in ["09:00-12:00", "12:00-15:00", "15:00-18:00"]:
                slot = ServiceSlot(
                    garage_id=garage.id,
                    date=date,
                    time_slot=slot_time,
                    is_available=random.random() > 0.3,
                    max_capacity=3,
                    current_bookings=random.randint(0, 2)
                )
                db.add(slot)
    db.commit()
    
    vehicles = [
        Vehicle(
            owner_id=1,
            registration_number="DL-01-AB-1234",
            make="Mahindra",
            model="XUV700",
            year=2023,
            vin="MAHTB12XPTC123456",
            engine_health=92.5,
            brake_health=88.0,
            battery_health=95.0,
            tire_health=85.0,
            last_service_date=datetime.now() - timedelta(days=120),
            total_km=15000,
            avg_km_per_month=1500,
            service_interval_km=10000,
            service_interval_months=6,
            latitude=28.6139,
            longitude=77.2090
        ),
        Vehicle(
            owner_id=1,
            registration_number="DL-01-CD-5678",
            make="Hero",
            model="Splendor Plus",
            year=2022,
            vin="HEROSPLD22B789012",
            engine_health=78.0,
            brake_health=65.0,
            battery_health=82.0,
            tire_health=70.0,
            last_service_date=datetime.now() - timedelta(days=200),
            total_km=25000,
            avg_km_per_month=2000,
            service_interval_km=6000,
            service_interval_months=4,
            latitude=28.6200,
            longitude=77.2150
        ),
        Vehicle(
            owner_id=2,
            registration_number="HR-26-EF-9012",
            make="Mahindra",
            model="Thar",
            year=2024,
            vin="MAHTHR24D345678",
            engine_health=98.0,
            brake_health=96.0,
            battery_health=99.0,
            tire_health=94.0,
            last_service_date=datetime.now() - timedelta(days=30),
            total_km=5000,
            avg_km_per_month=1000,
            service_interval_km=10000,
            service_interval_months=6,
            latitude=28.4595,
            longitude=77.0266
        ),
        Vehicle(
            owner_id=2,
            registration_number="HR-26-GH-3456",
            make="Hero",
            model="Xtreme 160R",
            year=2023,
            vin="HEROXT23F567890",
            engine_health=85.0,
            brake_health=80.0,
            battery_health=88.0,
            tire_health=75.0,
            last_service_date=datetime.now() - timedelta(days=90),
            total_km=12000,
            avg_km_per_month=1800,
            service_interval_km=6000,
            service_interval_months=4,
            latitude=28.4600,
            longitude=77.0300
        ),
        Vehicle(
            owner_id=3,
            registration_number="UP-16-IJ-7890",
            make="Mahindra",
            model="Scorpio N",
            year=2023,
            vin="MAHSCN23G901234",
            engine_health=45.0,
            brake_health=55.0,
            battery_health=70.0,
            tire_health=60.0,
            last_service_date=datetime.now() - timedelta(days=180),
            total_km=35000,
            avg_km_per_month=2500,
            service_interval_km=10000,
            service_interval_months=6,
            latitude=28.5707,
            longitude=77.3219
        )
    ]
    
    for vehicle in vehicles:
        db.add(vehicle)
    db.commit()
    
    service_types = ["Regular Service", "Oil Change", "Brake Inspection", "Engine Tune-up", "Full Service"]
    statuses = ["open", "in_progress", "completed"]
    
    service_requests = []
    for i in range(15):
        vehicle = random.choice(vehicles)
        garage = random.choice(garages)
        status = random.choice(statuses)
        
        created_date = datetime.now() - timedelta(days=random.randint(1, 60))
        scheduled_date = created_date + timedelta(days=random.randint(1, 7))
        completed_date = scheduled_date + timedelta(days=random.randint(0, 2)) if status == "completed" else None
        
        sr = ServiceRequest(
            vehicle_id=vehicle.id,
            garage_id=garage.id,
            service_type=random.choice(service_types),
            description="Routine maintenance service",
            requested_date=created_date,
            scheduled_date=scheduled_date,
            completed_date=completed_date,
            status=status,
            priority=random.choice(["low", "medium", "high"]),
            estimated_cost=random.randint(2000, 8000),
            actual_cost=random.randint(2000, 8000) if status == "completed" else None,
            estimated_hours=random.uniform(1, 4),
            actual_hours=random.uniform(1, 5) if status == "completed" else None
        )
        service_requests.append(sr)
        db.add(sr)
    db.commit()
    
    breakdown_types = ["Flat Tire", "Battery Dead", "Engine Overheating", "Brake Failure", "Electrical Issue", "Fuel Issue"]
    breakdown_statuses = ["reported", "garage_assigned", "garage_en_route", "repair_in_progress", "completed"]
    
    for i in range(10):
        vehicle = random.choice(vehicles)
        garage = random.choice(garages) if random.random() > 0.3 else None
        status = random.choice(breakdown_statuses)
        
        reported_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
        be = BreakdownEvent(
            vehicle_id=vehicle.id,
            garage_id=garage.id if garage else None,
            breakdown_type=random.choice(breakdown_types),
            description="Vehicle breakdown reported",
            vehicle_latitude=vehicle.latitude + random.uniform(-0.01, 0.01),
            vehicle_longitude=vehicle.longitude + random.uniform(-0.01, 0.01),
            status=status,
            reported_at=reported_at,
            garage_assigned_at=reported_at + timedelta(minutes=10) if garage else None,
            completed_at=reported_at + timedelta(hours=random.randint(1, 5)) if status == "completed" else None,
            estimated_arrival_minutes=random.randint(15, 45),
            estimated_repair_minutes=random.randint(30, 180),
            actual_repair_minutes=random.randint(30, 180) if status == "completed" else None,
            estimated_cost=random.randint(500, 5000),
            actual_cost=random.randint(500, 5000) if status == "completed" else None
        )
        db.add(be)
    db.commit()
    
    spare_parts = [
        SparePart(part_number="TIR-001", name="Tire 15 inch", category="Tires", oem_price=3500, aftermarket_price=2800, quantity_in_stock=20, breakdown_types="Flat Tire,Tire"),
        SparePart(part_number="TIR-002", name="Tire 16 inch", category="Tires", oem_price=4200, aftermarket_price=3400, quantity_in_stock=15, breakdown_types="Flat Tire,Tire"),
        SparePart(part_number="TUB-001", name="Tire Tube", category="Tires", oem_price=500, aftermarket_price=350, quantity_in_stock=30, breakdown_types="Flat Tire"),
        SparePart(part_number="BAT-001", name="Battery 12V 45Ah", category="Electrical", oem_price=5000, aftermarket_price=4000, quantity_in_stock=12, breakdown_types="Battery Dead,Battery"),
        SparePart(part_number="BAT-002", name="Battery 12V 60Ah", category="Electrical", oem_price=6500, aftermarket_price=5200, quantity_in_stock=8, breakdown_types="Battery Dead,Battery"),
        SparePart(part_number="BRK-001", name="Brake Pads Set (Front)", category="Brakes", oem_price=2500, aftermarket_price=1800, quantity_in_stock=25, breakdown_types="Brake Failure,Brake"),
        SparePart(part_number="BRK-002", name="Brake Pads Set (Rear)", category="Brakes", oem_price=2200, aftermarket_price=1600, quantity_in_stock=22, breakdown_types="Brake Failure,Brake"),
        SparePart(part_number="BRK-003", name="Brake Disc (Front)", category="Brakes", oem_price=3000, aftermarket_price=2400, quantity_in_stock=10, breakdown_types="Brake Failure"),
        SparePart(part_number="BRK-004", name="Brake Fluid 500ml", category="Fluids", oem_price=400, aftermarket_price=300, quantity_in_stock=40, breakdown_types="Brake Failure,Brake"),
        SparePart(part_number="ENG-001", name="Engine Oil 5L (Synthetic)", category="Fluids", oem_price=2500, aftermarket_price=2000, quantity_in_stock=35, breakdown_types="Engine,Regular Service"),
        SparePart(part_number="ENG-002", name="Oil Filter", category="Filters", oem_price=350, aftermarket_price=250, quantity_in_stock=50, breakdown_types="Engine,Regular Service"),
        SparePart(part_number="ENG-003", name="Air Filter", category="Filters", oem_price=450, aftermarket_price=350, quantity_in_stock=45, breakdown_types="Engine,Regular Service"),
        SparePart(part_number="ENG-004", name="Spark Plugs Set", category="Engine", oem_price=600, aftermarket_price=450, quantity_in_stock=30, breakdown_types="Engine,Regular Service"),
        SparePart(part_number="COL-001", name="Coolant 2L", category="Fluids", oem_price=600, aftermarket_price=450, quantity_in_stock=25, breakdown_types="Overheating,Engine Overheating"),
        SparePart(part_number="COL-002", name="Thermostat", category="Cooling", oem_price=1200, aftermarket_price=900, quantity_in_stock=8, breakdown_types="Overheating,Engine Overheating"),
        SparePart(part_number="COL-003", name="Radiator Hose", category="Cooling", oem_price=800, aftermarket_price=600, quantity_in_stock=12, breakdown_types="Overheating"),
        SparePart(part_number="ELC-001", name="Fuse Kit", category="Electrical", oem_price=300, aftermarket_price=200, quantity_in_stock=35, breakdown_types="Electrical Issue,Electrical"),
        SparePart(part_number="ELC-002", name="Alternator", category="Electrical", oem_price=6000, aftermarket_price=4500, quantity_in_stock=5, breakdown_types="Electrical Issue,Battery"),
        SparePart(part_number="ELC-003", name="Starter Motor", category="Electrical", oem_price=4500, aftermarket_price=3500, quantity_in_stock=6, breakdown_types="Electrical Issue,Starter"),
        SparePart(part_number="TRN-001", name="Transmission Fluid 1L", category="Fluids", oem_price=1200, aftermarket_price=900, quantity_in_stock=20, breakdown_types="Transmission"),
    ]
    
    for part in spare_parts:
        db.add(part)
    db.commit()
    
    for sr in service_requests:
        if sr.status == "completed":
            user = db.query(User).join(Vehicle).filter(Vehicle.id == sr.vehicle_id).first()
            if user:
                feedback = Feedback(
                    user_id=user.id,
                    service_request_id=sr.id,
                    rating=random.randint(3, 5),
                    comment="Good service experience.",
                    service_quality=random.randint(3, 5),
                    time_satisfaction=random.randint(3, 5),
                    cost_satisfaction=random.randint(3, 5),
                    would_recommend=random.random() > 0.2
                )
                db.add(feedback)
    db.commit()
    
    alert_types = [
        ("upcoming_service", "Service Due Soon", "Your vehicle service is due in a few days.", "medium"),
        ("overdue_service", "Service Overdue!", "Your vehicle service is overdue. Please schedule immediately.", "critical"),
        ("breakdown_risk", "Health Warning", "Vehicle health is low. Risk of breakdown.", "high"),
    ]
    
    for user in users[:3]:
        for _ in range(random.randint(1, 3)):
            alert_data = random.choice(alert_types)
            alert = Alert(
                user_id=user.id,
                vehicle_id=random.choice([v.id for v in vehicles if v.owner_id == user.id]) if any(v.owner_id == user.id for v in vehicles) else None,
                alert_type=alert_data[0],
                title=alert_data[1],
                message=alert_data[2],
                priority=alert_data[3],
                is_read=random.random() > 0.5,
                expires_at=datetime.now() + timedelta(days=7)
            )
            db.add(alert)
    db.commit()
    
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
