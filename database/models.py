from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
import os

Base = declarative_base()

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class AlertPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ServiceStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BreakdownStatus(enum.Enum):
    REPORTED = "reported"
    GARAGE_ASSIGNED = "garage_assigned"
    GARAGE_EN_ROUTE = "garage_en_route"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    COMPLETED = "completed"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    vehicles = relationship("Vehicle", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    registration_number = Column(String(20), unique=True, nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer)
    vin = Column(String(50))
    
    engine_health = Column(Float, default=100.0)
    brake_health = Column(Float, default=100.0)
    battery_health = Column(Float, default=100.0)
    tire_health = Column(Float, default=100.0)
    
    last_service_date = Column(DateTime)
    next_service_date = Column(DateTime)
    total_km = Column(Float, default=0)
    avg_km_per_month = Column(Float, default=1000)
    service_interval_km = Column(Integer, default=10000)
    service_interval_months = Column(Integer, default=6)
    
    latitude = Column(Float)
    longitude = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="vehicles")
    service_requests = relationship("ServiceRequest", back_populates="vehicle")
    breakdown_events = relationship("BreakdownEvent", back_populates="vehicle")

class Garage(Base):
    __tablename__ = 'garages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    city = Column(String(50))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    
    capacity = Column(Integer, default=10)
    current_load = Column(Integer, default=0)
    
    opening_time = Column(String(10), default="08:00")
    closing_time = Column(String(10), default="18:00")
    working_days = Column(String(50), default="Mon-Sat")
    
    supported_services = Column(Text)
    rating = Column(Float, default=4.0)
    avg_repair_time_hours = Column(Float, default=2.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    service_slots = relationship("ServiceSlot", back_populates="garage")
    service_requests = relationship("ServiceRequest", back_populates="garage")
    breakdown_events = relationship("BreakdownEvent", back_populates="garage")

class ServiceSlot(Base):
    __tablename__ = 'service_slots'
    
    id = Column(Integer, primary_key=True)
    garage_id = Column(Integer, ForeignKey('garages.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    time_slot = Column(String(20), nullable=False)
    is_available = Column(Boolean, default=True)
    max_capacity = Column(Integer, default=3)
    current_bookings = Column(Integer, default=0)
    
    garage = relationship("Garage", back_populates="service_slots")

class ServiceRequest(Base):
    __tablename__ = 'service_requests'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    garage_id = Column(Integer, ForeignKey('garages.id'))
    
    service_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    requested_date = Column(DateTime)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    status = Column(String(20), default='open')
    priority = Column(String(20), default='medium')
    
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="service_requests")
    garage = relationship("Garage", back_populates="service_requests")

class BreakdownEvent(Base):
    __tablename__ = 'breakdown_events'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    garage_id = Column(Integer, ForeignKey('garages.id'))
    
    breakdown_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    vehicle_latitude = Column(Float)
    vehicle_longitude = Column(Float)
    
    garage_current_lat = Column(Float)
    garage_current_lng = Column(Float)
    
    status = Column(String(30), default='reported')
    
    reported_at = Column(DateTime, default=datetime.utcnow)
    garage_assigned_at = Column(DateTime)
    garage_arrived_at = Column(DateTime)
    repair_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    estimated_arrival_minutes = Column(Integer)
    estimated_repair_minutes = Column(Integer)
    actual_repair_minutes = Column(Integer)
    
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    
    vehicle = relationship("Vehicle", back_populates="breakdown_events")
    garage = relationship("Garage", back_populates="breakdown_events")

class SparePart(Base):
    __tablename__ = 'spare_parts'
    
    id = Column(Integer, primary_key=True)
    part_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    
    oem_price = Column(Float, nullable=False)
    aftermarket_price = Column(Float)
    
    quantity_in_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=5)
    
    compatible_makes = Column(Text)
    compatible_models = Column(Text)
    
    breakdown_types = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))
    
    alert_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text)
    priority = Column(String(20), default='medium')
    
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="alerts")

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service_request_id = Column(Integer, ForeignKey('service_requests.id'))
    breakdown_event_id = Column(Integer, ForeignKey('breakdown_events.id'))
    
    rating = Column(Integer)
    comment = Column(Text)
    
    service_quality = Column(Integer)
    time_satisfaction = Column(Integer)
    cost_satisfaction = Column(Integer)
    
    would_recommend = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="feedback")

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    
    input_data = Column(Text)
    output_data = Column(Text)
    decision = Column(Text)
    
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///autosense.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    return SessionLocal()
